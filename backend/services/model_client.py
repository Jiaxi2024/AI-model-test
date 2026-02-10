"""模型 API 客户端封装：OpenAI 兼容接口、流式调用、超时处理

支持两种模式：
1. 预置模型 — 使用全局 DASHSCOPE_BASE_URL + DASHSCOPE_API_KEY
2. 自定义模型 — 使用 ModelConfig 中的 custom_base_url + custom_api_key
"""

import asyncio
import json
import time
from typing import AsyncGenerator

from openai import AsyncOpenAI

from backend.config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    MODEL_API_TIMEOUT,
)


# 运行时自定义 API Key 存储（内存级别，重启后失效）
_custom_api_key: str | None = None


def set_custom_api_key(api_key: str | None):
    """设置用户自定义的全局 API Key（覆盖 .env 配置）"""
    global _custom_api_key
    _custom_api_key = api_key


def get_custom_api_key() -> str | None:
    """获取当前自定义全局 API Key"""
    return _custom_api_key


def _get_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncOpenAI:
    """获取 OpenAI 兼容客户端

    Args:
        api_key: 指定 API Key（优先级最高）
        base_url: 指定 Base URL（如果为 None 则使用全局 DashScope URL）
    """
    key = api_key or _custom_api_key or DASHSCOPE_API_KEY
    if not key:
        raise ValueError("未配置 API Key，请在 .env 文件或设置页面中配置 DASHSCOPE_API_KEY")
    return AsyncOpenAI(
        api_key=key,
        base_url=base_url or DASHSCOPE_BASE_URL,
        timeout=MODEL_API_TIMEOUT,
    )


async def stream_chat_completion(
    model_id: str,
    messages: list[dict],
    params: dict | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncGenerator[dict, None]:
    """
    流式调用模型 API，返回增量事件流（统一格式）。

    自定义模型和预置模型的返回都被标准化为相同格式，
    同时收集 raw 原始 chunk 用于调试。

    Args:
        model_id: 模型标识符
        messages: OpenAI 格式 messages
        params: temperature / max_tokens / top_p 等
        api_key: 自定义模型的 API Key（None 则用全局）
        base_url: 自定义模型的 Base URL（None 则用 DashScope）

    Yields:
        dict: 标准化事件数据
            - {"type": "token", "text": "增量文本"}
            - {"type": "usage", "input_tokens": N, "output_tokens": N}
            - {"type": "done", "response_time_ms": N, "raw_chunks": [...]}
            - {"type": "error", "message": "错误描述", ...}
    """
    client = _get_client(api_key=api_key, base_url=base_url)
    params = params or {}
    start_time = time.time()

    # 收集原始 chunk 用于调试（只保留关键信息，不保留完整对象以避免过大）
    raw_chunks = []

    try:
        # 构建请求参数
        create_kwargs = dict(
            model=model_id,
            messages=messages,
            stream=True,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 2048),
            top_p=params.get("top_p", 1.0),
        )

        # stream_options 并非所有 provider 都支持，但 OpenAI 兼容的大部分支持
        # 对自定义模型也尝试启用，如果不支持会被忽略
        create_kwargs["stream_options"] = {"include_usage": True}

        stream = await asyncio.wait_for(
            client.chat.completions.create(**create_kwargs),
            timeout=MODEL_API_TIMEOUT,
        )

        input_tokens = 0
        output_tokens = 0

        async for chunk in stream:
            # 收集 raw（精简版）
            try:
                raw_chunks.append(_serialize_chunk(chunk))
            except Exception:
                pass  # raw 收集不应影响主流程

            # 标准化：提取增量文本
            if chunk.choices and chunk.choices[0].delta.content:
                yield {
                    "type": "token",
                    "text": chunk.choices[0].delta.content,
                }

            # 标准化：提取 usage 信息（通常在最后一个 chunk）
            if hasattr(chunk, "usage") and chunk.usage:
                input_tokens = chunk.usage.prompt_tokens or 0
                output_tokens = chunk.usage.completion_tokens or 0

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 发送 usage 事件
        if input_tokens or output_tokens:
            yield {
                "type": "usage",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        yield {
            "type": "done",
            "response_time_ms": elapsed_ms,
            "raw_chunks": raw_chunks,
        }

    except asyncio.TimeoutError:
        elapsed_ms = int((time.time() - start_time) * 1000)
        yield {
            "type": "error",
            "message": f"请求超时（{MODEL_API_TIMEOUT}秒），请稍后重试",
            "response_time_ms": elapsed_ms,
            "is_timeout": True,
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        yield {
            "type": "error",
            "message": str(e),
            "response_time_ms": elapsed_ms,
            "is_timeout": False,
        }


def _serialize_chunk(chunk) -> dict:
    """将 OpenAI chunk 对象序列化为可 JSON 的 dict（精简版，调试用）"""
    result = {}
    if hasattr(chunk, "id"):
        result["id"] = chunk.id
    if hasattr(chunk, "model"):
        result["model"] = chunk.model
    if chunk.choices:
        c = chunk.choices[0]
        delta = {}
        if c.delta.content:
            delta["content"] = c.delta.content[:200]  # 截断避免过大
        if c.delta.role:
            delta["role"] = c.delta.role
        if c.finish_reason:
            delta["finish_reason"] = c.finish_reason
        result["choice"] = delta
    if hasattr(chunk, "usage") and chunk.usage:
        result["usage"] = {
            "prompt_tokens": chunk.usage.prompt_tokens,
            "completion_tokens": chunk.usage.completion_tokens,
        }
    return result


def build_messages(
    text: str | None = None,
    file_urls: list[dict] | None = None,
) -> list[dict]:
    """
    构建 OpenAI 兼容的 messages 结构。

    对于自定义模型（纯 OpenAI 兼容），只传 text 和 image_url。
    对于 DashScope 特有的 audio/video 格式，也一并处理。

    Args:
        text: 文本输入
        file_urls: 文件信息列表

    Returns:
        messages 列表
    """
    content = []

    if text:
        content.append({"type": "text", "text": text})

    if file_urls:
        for file_info in file_urls:
            modality = file_info.get("modality", "image")
            url = file_info["url"]
            mime_type = file_info.get("mime_type", "")

            if modality == "image":
                content.append({
                    "type": "image_url",
                    "image_url": {"url": url},
                })
            elif modality == "video":
                content.append({
                    "type": "video_url",
                    "video_url": {"url": url},
                })
            elif modality == "audio":
                fmt = _audio_format_from_mime(mime_type)
                content.append({
                    "type": "input_audio",
                    "input_audio": {"data": url, "format": fmt},
                })

    if not content:
        content.append({"type": "text", "text": ""})

    return [{"role": "user", "content": content}]


def _audio_format_from_mime(mime_type: str) -> str:
    """从 MIME 类型推断音频格式名"""
    mapping = {
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/mp3": "mp3",
        "audio/mpeg": "mp3",
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/aac": "aac",
    }
    return mapping.get(mime_type, "wav")
