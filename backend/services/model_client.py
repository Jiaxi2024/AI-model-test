"""阿里云模型 API 客户端封装：OpenAI 兼容接口、流式调用、超时处理"""

import asyncio
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
    """设置用户自定义的 API Key"""
    global _custom_api_key
    _custom_api_key = api_key


def get_custom_api_key() -> str | None:
    """获取当前自定义 API Key"""
    return _custom_api_key


def _get_client(api_key: str | None = None) -> AsyncOpenAI:
    """获取 OpenAI 兼容客户端"""
    key = api_key or _custom_api_key or DASHSCOPE_API_KEY
    if not key:
        raise ValueError("未配置 API Key，请在 .env 文件或设置页面中配置 DASHSCOPE_API_KEY")
    return AsyncOpenAI(
        api_key=key,
        base_url=DASHSCOPE_BASE_URL,
        timeout=MODEL_API_TIMEOUT,
    )


async def stream_chat_completion(
    model_id: str,
    messages: list[dict],
    params: dict | None = None,
    api_key: str | None = None,
) -> AsyncGenerator[dict, None]:
    """
    流式调用模型 API，返回增量事件流。

    Yields:
        dict: 事件数据
            - {"type": "token", "text": "增量文本"}
            - {"type": "audio", "audio_url": "音频URL"}
            - {"type": "usage", "input_tokens": N, "output_tokens": N}
            - {"type": "done", "response_time_ms": N}
            - {"type": "error", "message": "错误描述"}
    """
    client = _get_client(api_key)
    params = params or {}
    start_time = time.time()

    try:
        stream = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("max_tokens", 2048),
                top_p=params.get("top_p", 1.0),
            ),
            timeout=MODEL_API_TIMEOUT,
        )

        input_tokens = 0
        output_tokens = 0

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {
                    "type": "token",
                    "text": chunk.choices[0].delta.content,
                }

            # 处理 usage 信息（通常在最后一个 chunk）
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


def build_messages(
    text: str | None = None,
    file_urls: list[dict] | None = None,
) -> list[dict]:
    """
    构建 OpenAI 兼容的 messages 结构（适配阿里云 DashScope）。

    Args:
        text: 文本输入
        file_urls: 文件信息列表
            [{"modality": "image", "url": "data:image/png;base64,...", "mime_type": "image/png"}, ...]

    Returns:
        messages 列表
    """
    content = []

    if text:
        content.append({"type": "text", "text": text})

    if file_urls:
        for file_info in file_urls:
            modality = file_info.get("modality", "image")
            url = file_info["url"]           # base64 data URL
            mime_type = file_info.get("mime_type", "")

            if modality == "image":
                # DashScope 格式: data:image/png;base64,xxx
                content.append({
                    "type": "image_url",
                    "image_url": {"url": url},
                })
            elif modality == "video":
                # DashScope 格式: data:;base64,xxx
                content.append({
                    "type": "video_url",
                    "video_url": {"url": url},
                })
            elif modality == "audio":
                # DashScope 格式: input_audio.data = "data:;base64,xxx"
                # format 根据实际文件类型推断
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
