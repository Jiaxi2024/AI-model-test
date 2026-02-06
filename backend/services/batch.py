"""批量测试服务：逐一拼接关键词+模板、调用模型、更新进度"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    ModelConfig,
    TestInput,
    TestRecord,
    KeywordBatch,
    InputType,
    RecordStatus,
    BatchStatus,
)
from backend.services.model_client import stream_chat_completion, build_messages


async def create_batch(
    db: AsyncSession,
    model_config_id: str,
    keywords: list[str],
    prompt_template: str,
    params: dict | None = None,
) -> dict:
    """创建批量测试任务"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == model_config_id)
    )
    model_config = result.scalar_one_or_none()
    if not model_config:
        raise ValueError("模型配置未找到")

    batch = KeywordBatch(
        model_config_id=model_config_id,
        keywords=keywords,
        prompt_template=prompt_template,
        custom_params=params or {},
        total_count=len(keywords),
        status=BatchStatus.PENDING,
    )
    db.add(batch)
    await db.flush()

    return {
        "id": batch.id,
        "status": batch.status.value,
        "total_count": batch.total_count,
        "completed_count": 0,
        "failed_count": 0,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
    }


async def get_batch_detail(db: AsyncSession, batch_id: str) -> dict | None:
    """获取批量测试任务详情"""
    result = await db.execute(
        select(KeywordBatch).where(KeywordBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        return None

    # 获取关联的测试记录
    records_result = await db.execute(
        select(TestRecord).where(TestRecord.keyword_batch_id == batch_id)
    )
    records = records_result.scalars().all()

    results = []
    for i, keyword in enumerate(batch.keywords):
        record = next((r for r in records if r.prompt_text and keyword in r.prompt_text), None)
        results.append({
            "keyword": keyword,
            "output": record.output_text if record else None,
            "status": (record.status.value if record and hasattr(record.status, 'value') else record.status) if record else "pending",
            "token_input": record.token_input if record else 0,
            "token_output": record.token_output if record else 0,
            "error_message": record.error_message if record else None,
        })

    return {
        "id": batch.id,
        "status": batch.status.value if hasattr(batch.status, 'value') else batch.status,
        "total_count": batch.total_count,
        "completed_count": batch.completed_count,
        "failed_count": batch.failed_count,
        "keywords": batch.keywords,
        "prompt_template": batch.prompt_template,
        "results": results,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
    }


async def stream_batch(
    db: AsyncSession,
    batch_id: str,
) -> AsyncGenerator[tuple[str, dict], None]:
    """流式执行批量测试，返回 (event_type, event_data) 元组流"""
    result = await db.execute(
        select(KeywordBatch).where(KeywordBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        yield ("error", {"message": "批量任务未找到"})
        return

    mc_result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == batch.model_config_id)
    )
    model_config = mc_result.scalar_one_or_none()
    if not model_config:
        yield ("error", {"message": "模型配置未找到"})
        return

    batch.status = BatchStatus.RUNNING
    await db.flush()

    merged_params = {**model_config.default_params, **(batch.custom_params or {})}

    for idx, keyword in enumerate(batch.keywords):
        prompt = batch.prompt_template.replace("{keyword}", keyword)

        # 发送进度（sleep(0) 确保事件能及时 flush 到客户端）
        yield ("progress", {
            "completed": batch.completed_count,
            "total": batch.total_count,
            "current_keyword": keyword,
        })
        await asyncio.sleep(0)

        # 创建 TestInput + TestRecord
        test_input = TestInput(text_content=prompt, input_type=InputType.BATCH)
        db.add(test_input)
        await db.flush()

        record = TestRecord(
            model_config_id=model_config.id,
            test_input_id=test_input.id,
            custom_params=merged_params,
            prompt_text=prompt,
            status=RecordStatus.RUNNING,
            keyword_batch_id=batch.id,
        )
        db.add(record)
        await db.flush()

        # 调用模型
        full_text = ""
        try:
            messages = build_messages(text=prompt)
            async for event in stream_chat_completion(
                model_id=model_config.model_id,
                messages=messages,
                params=merged_params,
            ):
                if event["type"] == "token":
                    full_text += event["text"]
                elif event["type"] == "usage":
                    record.token_input = event.get("input_tokens", 0)
                    record.token_output = event.get("output_tokens", 0)
                elif event["type"] == "done":
                    record.response_time_ms = event.get("response_time_ms", 0)
                elif event["type"] == "error":
                    raise Exception(event["message"])

            record.output_text = full_text
            record.status = RecordStatus.SUCCESS
            batch.completed_count += 1

            yield ("result", {
                "keyword": keyword,
                "output": full_text[:200],
                "status": "success",
                "token_input": record.token_input,
                "token_output": record.token_output,
            })
            await asyncio.sleep(0)

        except Exception as e:
            record.error_message = str(e)
            record.status = RecordStatus.FAILED
            record.output_text = full_text
            batch.failed_count += 1
            batch.completed_count += 1

            yield ("result", {
                "keyword": keyword,
                "output": None,
                "status": "failed",
                "error_message": str(e),
            })
            await asyncio.sleep(0)

        await db.flush()

    # 完成
    batch.status = BatchStatus.COMPLETED
    batch.completed_at = datetime.now(timezone.utc)
    await db.flush()

    yield ("done", {
        "batch_id": batch.id,
        "completed": batch.completed_count,
        "failed": batch.failed_count,
    })


async def export_batch(db: AsyncSession, batch_id: str, fmt: str = "csv") -> str | list:
    """导出批量测试结果"""
    detail = await get_batch_detail(db, batch_id)
    if not detail:
        raise ValueError("批量任务未找到")

    if fmt == "json":
        return detail["results"]

    # CSV 格式
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["关键词", "状态", "输出", "输入Token", "输出Token", "错误信息"])
    for r in detail["results"]:
        writer.writerow([
            r["keyword"],
            r["status"],
            r.get("output", ""),
            r.get("token_input", 0),
            r.get("token_output", 0),
            r.get("error_message", ""),
        ])
    return output.getvalue()
