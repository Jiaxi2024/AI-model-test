"""模型列表 API 路由：GET 列表 + CRUD 自定义模型 + Test Connection"""

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel as PydanticModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.model_config import ModelConfig

router = APIRouter(prefix="/models", tags=["models"])


# ---- Pydantic 请求体 ----

class CustomModelCreate(PydanticModel):
    """创建自定义模型的请求体"""
    name: str
    model_id: str
    base_url: str
    api_key: str
    supported_modalities: list[str] = ["text"]
    default_params: dict = {"temperature": 0.7, "max_tokens": 2048}


class CustomModelUpdate(PydanticModel):
    """更新自定义模型的请求体（所有字段可选）"""
    name: str | None = None
    model_id: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    supported_modalities: list[str] | None = None
    default_params: dict | None = None
    is_active: bool | None = None


class TestConnectionRequest(PydanticModel):
    """测试连接的请求体"""
    base_url: str
    api_key: str
    model_id: str


# ---- 路由 ----

@router.get("")
async def list_models(db: AsyncSession = Depends(get_db)):
    """获取可用模型列表（预置 + 自定义）"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.is_active == True).order_by(ModelConfig.is_custom, ModelConfig.name)
    )
    models = result.scalars().all()

    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "model_id": m.model_id,
                "provider": m.provider,
                "supported_modalities": m.supported_modalities,
                "default_params": m.default_params,
                "is_active": m.is_active,
                "is_custom": m.is_custom,
                # 自定义模型额外返回 base_url（API Key 脱敏）
                "custom_base_url": m.custom_base_url if m.is_custom else None,
                "custom_api_key_set": bool(m.custom_api_key) if m.is_custom else None,
            }
            for m in models
        ]
    }


@router.get("/{model_config_id}")
async def get_model(model_config_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个模型详情"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == model_config_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="模型未找到")

    resp = {
        "id": model.id,
        "name": model.name,
        "model_id": model.model_id,
        "provider": model.provider,
        "api_endpoint": model.api_endpoint,
        "supported_modalities": model.supported_modalities,
        "default_params": model.default_params,
        "is_active": model.is_active,
        "is_custom": model.is_custom,
    }
    if model.is_custom:
        resp["custom_base_url"] = model.custom_base_url
        resp["custom_api_key_masked"] = _mask_key(model.custom_api_key)
    return resp


@router.post("")
async def create_custom_model(
    body: CustomModelCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加自定义模型（仅支持 OpenAI-compatible API）"""
    # 去除 base_url 末尾的斜杠
    base_url = body.base_url.rstrip("/")

    model = ModelConfig(
        name=body.name,
        model_id=body.model_id,
        provider="custom",
        api_endpoint=base_url,
        default_params=body.default_params,
        supported_modalities=body.supported_modalities,
        is_active=True,
        is_custom=True,
        custom_api_key=body.api_key,
        custom_base_url=base_url,
    )
    db.add(model)
    await db.flush()

    return {
        "id": model.id,
        "name": model.name,
        "model_id": model.model_id,
        "provider": model.provider,
        "is_custom": True,
        "message": "自定义模型添加成功",
    }


@router.put("/{model_config_id}")
async def update_custom_model(
    model_config_id: str,
    body: CustomModelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新自定义模型配置"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == model_config_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="模型未找到")
    if not model.is_custom:
        raise HTTPException(status_code=403, detail="预置模型不可编辑")

    if body.name is not None:
        model.name = body.name
    if body.model_id is not None:
        model.model_id = body.model_id
    if body.base_url is not None:
        base_url = body.base_url.rstrip("/")
        model.custom_base_url = base_url
        model.api_endpoint = base_url
    if body.api_key is not None:
        model.custom_api_key = body.api_key
    if body.supported_modalities is not None:
        model.supported_modalities = body.supported_modalities
    if body.default_params is not None:
        model.default_params = body.default_params
    if body.is_active is not None:
        model.is_active = body.is_active

    await db.flush()
    return {"message": "更新成功", "id": model.id}


@router.delete("/{model_config_id}")
async def delete_custom_model(
    model_config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除自定义模型"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == model_config_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="模型未找到")
    if not model.is_custom:
        raise HTTPException(status_code=403, detail="预置模型不可删除")

    # 软删除（标记为不活跃）
    model.is_active = False
    await db.flush()
    return {"message": "已删除", "id": model.id}


@router.post("/test-connection")
async def test_connection(body: TestConnectionRequest):
    """
    测试自定义模型的连接是否正常。
    发送一个简短的非流式请求来验证 base_url、api_key、model_id 是否有效。
    """
    base_url = body.base_url.rstrip("/")
    client = AsyncOpenAI(
        api_key=body.api_key,
        base_url=base_url,
        timeout=15,
    )

    start = time.time()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=body.model_id,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                stream=False,
            ),
            timeout=15,
        )
        elapsed_ms = int((time.time() - start) * 1000)

        # 提取返回信息
        text = ""
        if response.choices and response.choices[0].message.content:
            text = response.choices[0].message.content[:100]

        return {
            "success": True,
            "message": f"连接成功 ({elapsed_ms}ms)",
            "response_preview": text,
            "model": response.model if hasattr(response, "model") else body.model_id,
            "elapsed_ms": elapsed_ms,
        }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": "连接超时（15秒），请检查 Base URL 是否正确",
            "elapsed_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
            "elapsed_ms": int((time.time() - start) * 1000),
        }


def _mask_key(key: str | None) -> str:
    """脱敏 API Key"""
    if not key:
        return ""
    if len(key) <= 8:
        return key[:2] + "***"
    return key[:4] + "****" + key[-4:]
