"""模型对比服务：并行调用两组模型 API、合并 SSE 流"""

import asyncio
import json
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    ModelConfig,
    TestInput,
    TestRecord,
    UploadedFile,
    ComparisonSession,
    ComparisonGroup,
    InputType,
    RecordStatus,
    ComparisonStatus,
)
from backend.services.model_client import stream_chat_completion, build_messages
from backend.services.file_manager import get_file_base64_url


async def run_comparison(
    db: AsyncSession,
    text: str | None,
    file_ids: list[str],
    groups: list[dict],
) -> AsyncGenerator[tuple[str, dict], None]:
    """
    执行双模型对比，返回 (event_type, event_data) 元组流。
    """
    # 1. 获取两组模型配置
    model_configs = []
    for g in groups:
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.id == g["model_config_id"])
        )
        mc = result.scalar_one_or_none()
        if not mc:
            yield ("error", {"message": f"模型配置未找到: {g['model_config_id']}"})
            return
        model_configs.append(mc)

    # 2. 处理文件 — 转为 base64 data URL 供模型 API 使用
    file_urls = []
    if file_ids:
        for fid in file_ids:
            result = await db.execute(select(UploadedFile).where(UploadedFile.id == fid))
            uf = result.scalar_one_or_none()
            if uf:
                modality = uf.modality.value if hasattr(uf.modality, 'value') else uf.modality
                data_url = get_file_base64_url(uf.file_path, uf.mime_type)
                file_urls.append({
                    "modality": modality,
                    "url": data_url,
                    "mime_type": uf.mime_type,
                })

    # 3. 创建共用 TestInput
    test_input = TestInput(text_content=text, input_type=InputType.COMPARISON)
    db.add(test_input)
    await db.flush()

    # 4. 创建 ComparisonSession
    session = ComparisonSession(
        test_input_id=test_input.id,
        status=ComparisonStatus.RUNNING,
    )
    db.add(session)
    await db.flush()

    # 5. 创建两组 TestRecord + ComparisonGroup
    records = []
    comp_groups = []
    for idx, (g, mc) in enumerate(zip(groups, model_configs)):
        merged_params = {**mc.default_params, **(g.get("params") or {})}
        record = TestRecord(
            model_config_id=mc.id,
            test_input_id=test_input.id,
            custom_params=merged_params,
            prompt_text=text,
            status=RecordStatus.RUNNING,
            comparison_session_id=session.id,
        )
        db.add(record)
        await db.flush()

        cg = ComparisonGroup(
            comparison_session_id=session.id,
            model_config_id=mc.id,
            custom_params=merged_params,
            group_index=idx,
            test_record_id=record.id,
        )
        db.add(cg)
        records.append(record)
        comp_groups.append(cg)

    await db.flush()

    # 6. 构建 messages
    messages = build_messages(text=text, file_urls=file_urls if file_urls else None)

    # 7. 并行调用两组模型，通过 queue 合并事件
    queue = asyncio.Queue()

    async def stream_group(group_idx, model_config, params, record):
        full_text = ""
        # 解析自定义模型参数
        custom_base = model_config.custom_base_url if model_config.is_custom else None
        custom_key = model_config.custom_api_key if model_config.is_custom else None

        try:
            async for event in stream_chat_completion(
                model_id=model_config.model_id,
                messages=messages,
                params=params,
                api_key=custom_key,
                base_url=custom_base,
            ):
                event["group"] = group_idx
                if event["type"] == "token":
                    full_text += event["text"]
                await queue.put(event)

            record.output_text = full_text
            record.status = RecordStatus.SUCCESS
        except Exception as e:
            record.error_message = str(e)
            record.status = RecordStatus.FAILED
            await queue.put({"type": "error", "group": group_idx, "message": str(e)})

    # 启动两个并行任务
    tasks = []
    for idx, (g, mc, record) in enumerate(zip(groups, model_configs, records)):
        merged_params = {**mc.default_params, **(g.get("params") or {})}
        tasks.append(asyncio.create_task(
            stream_group(idx, mc, merged_params, record)
        ))

    async def wait_all():
        await asyncio.gather(*tasks)
        await queue.put(None)  # 哨兵值

    asyncio.create_task(wait_all())

    while True:
        event = await queue.get()
        if event is None:
            break

        event_type = event.get("type")
        group = event.get("group", 0)

        if event_type == "token":
            yield ("token", {"group": group, "text": event["text"]})
        elif event_type == "audio":
            yield ("audio", {"group": group, "audio_url": event["audio_url"]})
        elif event_type == "usage":
            records[group].token_input = event.get("input_tokens", 0)
            records[group].token_output = event.get("output_tokens", 0)
            yield ("usage", {
                "group": group,
                "input_tokens": event.get("input_tokens", 0),
                "output_tokens": event.get("output_tokens", 0),
            })
        elif event_type == "done":
            records[group].response_time_ms = event.get("response_time_ms", 0)
            # 保留 raw 原始返回
            raw_chunks = event.get("raw_chunks")
            if raw_chunks:
                try:
                    records[group].raw_response = json.dumps(raw_chunks, ensure_ascii=False)
                except Exception:
                    pass
        elif event_type == "error":
            yield ("error", {"group": group, "message": event["message"]})

    # 更新 session 状态
    await db.flush()
    all_success = all(r.status == RecordStatus.SUCCESS for r in records)
    session.status = ComparisonStatus.COMPLETED if all_success else ComparisonStatus.FAILED
    await db.flush()

    # 发送最终 done
    yield ("done", {
        "session_id": session.id,
        "groups": [
            {
                "group": idx,
                "record_id": r.id,
                "response_time_ms": r.response_time_ms,
                "token_input": r.token_input,
                "token_output": r.token_output,
                "status": r.status.value if hasattr(r.status, 'value') else r.status,
            }
            for idx, r in enumerate(records)
        ],
    })
