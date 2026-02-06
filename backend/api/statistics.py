"""统计 API 路由"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.statistics import get_overview, get_usage_stats

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    """获取总览统计数据"""
    return await get_overview(db)


@router.get("/usage")
async def usage(
    group_by: str = Query(default="model", pattern="^(model|day|week|month)$"),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """获取用量分布数据"""
    return await get_usage_stats(db, group_by, start_date, end_date)
