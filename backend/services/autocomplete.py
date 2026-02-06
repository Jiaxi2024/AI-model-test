"""AI 自动补全服务：调用轻量模型生成建议"""

from openai import AsyncOpenAI

from backend.config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    AUTOCOMPLETE_MODEL,
    AUTOCOMPLETE_MAX_TOKENS,
    MODEL_API_TIMEOUT,
)
from backend.services.model_client import _custom_api_key


async def get_suggestions(text: str, max_suggestions: int = 3) -> list[str]:
    """
    获取 AI 自动补全建议。

    Args:
        text: 当前输入文本
        max_suggestions: 最大建议数

    Returns:
        建议文本列表
    """
    if not text or len(text.strip()) < 2:
        return []

    key = _custom_api_key or DASHSCOPE_API_KEY
    if not key:
        return []

    client = AsyncOpenAI(
        api_key=key,
        base_url=DASHSCOPE_BASE_URL,
        timeout=10,  # 自动补全需要更快响应
    )

    try:
        response = await client.chat.completions.create(
            model=AUTOCOMPLETE_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个文本补全助手。用户正在输入一段提示词，"
                        "请根据已输入的内容，给出最可能的补全建议。"
                        f"只返回补全部分（不含用户已输入的文字），最多 {max_suggestions} 条，"
                        "每条用换行符分隔。只返回补全文本，不要编号或额外说明。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"请补全以下文本：\n{text}",
                },
            ],
            max_tokens=AUTOCOMPLETE_MAX_TOKENS,
            temperature=0.3,
        )

        result_text = response.choices[0].message.content or ""
        suggestions = [
            s.strip() for s in result_text.strip().split("\n") if s.strip()
        ]
        return suggestions[:max_suggestions]

    except Exception:
        # 自动补全失败不应影响用户体验
        return []
