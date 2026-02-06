"""推理 API 路由：POST /api/inference（SSE 流式响应）"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.inference import InferenceRequest
from backend.services.inference import run_inference

router = APIRouter(tags=["inference"])


@router.post("/inference")
async def create_inference(
    request: InferenceRequest,
    db: AsyncSession = Depends(get_db),
):
    """发起单次模型推理请求（流式 SSE 响应）"""
    if not request.text and not request.file_ids:
        raise HTTPException(status_code=400, detail="请输入文本或上传文件")

    async def event_generator():
        async for event_type, event_data in run_inference(
            db=db,
            model_config_id=request.model_config_id,
            text=request.text,
            file_ids=request.file_ids,
            params=request.params,
        ):
            yield ServerSentEvent(
                data=json.dumps(event_data, ensure_ascii=False),
                event=event_type,
            )

    return EventSourceResponse(event_generator())
