"""自动补全 API 路由"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.autocomplete import get_suggestions

router = APIRouter(tags=["autocomplete"])


class AutocompleteRequest(BaseModel):
    """自动补全请求"""
    text: str = Field(description="当前输入文本")
    max_suggestions: int = Field(default=3, ge=1, le=5, description="最大建议数")


@router.post("/autocomplete")
async def autocomplete(request: AutocompleteRequest):
    """获取 AI 自动补全建议"""
    suggestions = await get_suggestions(
        text=request.text,
        max_suggestions=request.max_suggestions,
    )
    return {"suggestions": suggestions}
