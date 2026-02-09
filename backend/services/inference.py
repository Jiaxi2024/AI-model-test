"""单次推理服务：接收多模态输入、构建 API 请求、流式调用模型、保存 TestRecord"""

import json
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    ModelConfig,
    TestInput,
    TestRecord,
    UploadedFile,
    InputType,
    RecordStatus,
)
from backend.services.model_client import stream_chat_completion, build_messages
from backend.services.file_manager import get_file_base64_url


async def run_inference(
    db: AsyncSession,
    model_config_id: str,
    text: str | None = None,
    file_ids: list[str] | None = None,
    params: dict | None = None,
) -> AsyncGenerator[tuple[str, dict], None]:
    """
    执行单次推理，返回 (event_type, event_data) 元组流。

    Yields:
        (event_type, event_data): 如 ("token", {"text": "..."})
    """
    # 1. 获取模型配置
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == model_config_id)
    )
    model_config = result.scalar_one_or_none()
    if not model_config:
        yield ("error", {"message": "模型配置未找到"})
        return

    # 2. 解析自定义模型的 base_url / api_key
    custom_base_url = model_config.custom_base_url if model_config.is_custom else None
    custom_api_key = model_config.custom_api_key if model_config.is_custom else None

    # 3. 处理输入内容 — 将本地文件转为 base64 data URL 供模型 API 使用
    file_urls = []
    if file_ids:
        for fid in file_ids:
            result = await db.execute(
                select(UploadedFile).where(UploadedFile.id == fid)
            )
            uploaded = result.scalar_one_or_none()
            if uploaded:
                modality = uploaded.modality.value if hasattr(uploaded.modality, 'value') else uploaded.modality
                data_url = get_file_base64_url(uploaded.file_path, uploaded.mime_type)
                file_urls.append({
                    "modality": modality,
                    "url": data_url,
                    "mime_type": uploaded.mime_type,
                })

    # 4. 创建 TestInput
    test_input = TestInput(
        text_content=text,
        input_type=InputType.SINGLE,
    )
    db.add(test_input)
    await db.flush()

    # 5. 创建 TestRecord (pending)
    merged_params = {**model_config.default_params, **(params or {})}
    test_record = TestRecord(
        model_config_id=model_config_id,
        test_input_id=test_input.id,
        custom_params=merged_params,
        prompt_text=text,
        status=RecordStatus.PENDING,
    )
    db.add(test_record)
    await db.flush()

    # 6. 更新状态为 running
    test_record.status = RecordStatus.RUNNING
    await db.flush()

    # 7. 构建 messages 并调用模型
    messages = build_messages(text=text, file_urls=file_urls if file_urls else None)

    full_text = ""
    input_tokens = 0
    output_tokens = 0
    response_time_ms = 0

    try:
        async for event in stream_chat_completion(
            model_id=model_config.model_id,
            messages=messages,
            params=merged_params,
            api_key=custom_api_key,
            base_url=custom_base_url,
        ):
            event_type = event.get("type")

            if event_type == "token":
                full_text += event["text"]
                yield ("token", {"text": event["text"]})

            elif event_type == "audio":
                yield ("audio", {"audio_url": event["audio_url"]})

            elif event_type == "usage":
                input_tokens = event.get("input_tokens", 0)
                output_tokens = event.get("output_tokens", 0)
                yield ("usage", {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                })

            elif event_type == "done":
                response_time_ms = event.get("response_time_ms", 0)
                raw_chunks = event.get("raw_chunks")

                # 更新记录
                test_record.output_text = full_text
                test_record.token_input = input_tokens
                test_record.token_output = output_tokens
                test_record.response_time_ms = response_time_ms
                test_record.status = RecordStatus.SUCCESS

                # 保留 raw 原始返回（调试用）
                if raw_chunks:
                    try:
                        test_record.raw_response = json.dumps(raw_chunks, ensure_ascii=False)
                    except Exception:
                        pass

                await db.flush()

                yield ("done", {
                    "record_id": test_record.id,
                    "response_time_ms": response_time_ms,
                })

            elif event_type == "error":
                response_time_ms = event.get("response_time_ms", 0)
                is_timeout = event.get("is_timeout", False)
                test_record.error_message = event["message"]
                test_record.response_time_ms = response_time_ms
                test_record.status = RecordStatus.TIMEOUT if is_timeout else RecordStatus.FAILED
                test_record.output_text = full_text
                await db.flush()

                yield ("error", {"message": event["message"]})

    except Exception as e:
        test_record.error_message = str(e)
        test_record.status = RecordStatus.FAILED
        test_record.output_text = full_text
        await db.flush()
        yield ("error", {"message": str(e)})
