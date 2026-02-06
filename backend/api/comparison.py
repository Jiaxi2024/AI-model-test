"""对比 API 路由：POST /api/comparison（SSE 流式响应）"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.comparison import ComparisonRequest
from backend.services.comparison import run_comparison

router = APIRouter(tags=["comparison"])


@router.post("/comparison")
async def create_comparison(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """发起双模型对比测试（流式 SSE 响应）"""
    if not request.text and not request.file_ids:
        raise HTTPException(status_code=400, detail="请输入文本或上传文件")

    if len(request.groups) != 2:
        raise HTTPException(status_code=400, detail="需要恰好两组模型配置")

    async def event_generator():
        async for event_type, event_data in run_comparison(
            db=db,
            text=request.text,
            file_ids=request.file_ids,
            groups=[g.model_dump() for g in request.groups],
        ):
            yield ServerSentEvent(
                data=json.dumps(event_data, ensure_ascii=False),
                event=event_type,
            )

    return EventSourceResponse(event_generator())
