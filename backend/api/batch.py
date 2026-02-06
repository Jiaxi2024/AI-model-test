"""批量测试 API 路由"""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.batch import BatchRequest
from backend.services.batch import (
    create_batch,
    get_batch_detail,
    stream_batch,
    export_batch,
)

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("")
async def create_batch_task(
    request: BatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建关键词批量测试任务"""
    try:
        result = await create_batch(
            db=db,
            model_config_id=request.model_config_id,
            keywords=request.keywords,
            prompt_template=request.prompt_template,
            params=request.params,
        )
        return JSONResponse(content=result, status_code=201)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{batch_id}")
async def get_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    """获取批量测试任务状态和结果"""
    detail = await get_batch_detail(db, batch_id)
    if not detail:
        raise HTTPException(status_code=404, detail="批量任务未找到")
    return detail


@router.get("/{batch_id}/stream")
async def stream_batch_progress(batch_id: str, db: AsyncSession = Depends(get_db)):
    """流式获取批量测试进度（SSE）"""

    async def event_generator():
        async for event_type, event_data in stream_batch(db, batch_id):
            yield ServerSentEvent(
                data=json.dumps(event_data, ensure_ascii=False),
                event=event_type,
            )

    return EventSourceResponse(event_generator())


@router.get("/{batch_id}/export")
async def export_batch_results(
    batch_id: str,
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
):
    """导出批量测试结果"""
    try:
        result = await export_batch(db, batch_id, format)
        if format == "json":
            return JSONResponse(content=result)
        return PlainTextResponse(
            content=result,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.csv"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
