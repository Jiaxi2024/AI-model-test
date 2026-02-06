"""设置 API 路由"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.model_client import set_custom_api_key, get_custom_api_key
from backend.config import DASHSCOPE_API_KEY

router = APIRouter(prefix="/settings", tags=["settings"])


class SetApiKeyRequest(BaseModel):
    """设置 API Key 请求"""
    api_key: str = Field(description="阿里云 DashScope API Key")


def _mask_key(key: str) -> str:
    """脱敏 API Key"""
    if not key or len(key) < 8:
        return "****"
    return key[:3] + "****" + key[-4:]


@router.post("/api-key")
async def set_api_key(request: SetApiKeyRequest):
    """设置用户自定义 API Key"""
    set_custom_api_key(request.api_key)
    return {
        "message": "API Key 已设置",
        "masked_key": _mask_key(request.api_key),
    }


@router.delete("/api-key")
async def clear_api_key():
    """清除用户自定义 API Key"""
    set_custom_api_key(None)
    return {
        "message": "已恢复使用服务端默认 API Key",
        "masked_key": _mask_key(DASHSCOPE_API_KEY) if DASHSCOPE_API_KEY else None,
    }


@router.get("/api-key")
async def get_api_key_status():
    """获取当前 API Key 状态"""
    custom = get_custom_api_key()
    if custom:
        return {
            "source": "custom",
            "masked_key": _mask_key(custom),
        }
    elif DASHSCOPE_API_KEY:
        return {
            "source": "server",
            "masked_key": _mask_key(DASHSCOPE_API_KEY),
        }
    else:
        return {
            "source": "none",
            "masked_key": None,
        }
