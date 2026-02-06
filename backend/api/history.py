"""历史记录 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.history import BatchDeleteRequest
from backend.services.history import (
    list_history,
    get_record_detail,
    delete_record,
    batch_delete_records,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def get_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    model_id: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """获取历史测试记录列表"""
    return await list_history(
        db, page=page, page_size=page_size,
        model_id=model_id, keyword=keyword,
        start_date=start_date, end_date=end_date, status=status,
    )


@router.get("/{record_id}")
async def get_history_detail(record_id: str, db: AsyncSession = Depends(get_db)):
    """获取单条历史记录详情"""
    detail = await get_record_detail(db, record_id)
    if not detail:
        raise HTTPException(status_code=404, detail="记录未找到")
    return detail


@router.delete("/{record_id}", status_code=204)
async def delete_history_record(record_id: str, db: AsyncSession = Depends(get_db)):
    """删除单条历史记录"""
    deleted = await delete_record(db, record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录未找到")


@router.post("/batch-delete")
async def batch_delete(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量删除历史记录"""
    count = await batch_delete_records(
        db,
        record_ids=request.record_ids if request.record_ids else None,
        delete_all=request.delete_all,
    )
    return {"deleted_count": count}
