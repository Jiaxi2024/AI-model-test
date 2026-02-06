"""模型列表 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.model_config import ModelConfig

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def list_models(db: AsyncSession = Depends(get_db)):
    """获取可用模型列表"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.is_active == True).order_by(ModelConfig.name)
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
            }
            for m in models
        ]
    }


@router.get("/{model_id}")
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个模型详情"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="模型未找到")

    return {
        "id": model.id,
        "name": model.name,
        "model_id": model.model_id,
        "provider": model.provider,
        "api_endpoint": model.api_endpoint,
        "supported_modalities": model.supported_modalities,
        "default_params": model.default_params,
        "is_active": model.is_active,
    }
