"""统计聚合服务"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import TestRecord, ModelConfig, RecordStatus


async def get_overview(db: AsyncSession) -> dict:
    """获取总览统计数据"""
    result = await db.execute(
        select(
            func.count(TestRecord.id).label("total_tests"),
            func.coalesce(func.sum(TestRecord.token_input), 0).label("total_tokens_input"),
            func.coalesce(func.sum(TestRecord.token_output), 0).label("total_tokens_output"),
            func.coalesce(func.avg(
                case(
                    (TestRecord.status == RecordStatus.SUCCESS, TestRecord.response_time_ms),
                    else_=None,
                )
            ), 0).label("avg_response_time_ms"),
        )
    )
    row = result.one()

    # 使用的模型数
    models_result = await db.execute(
        select(func.count(func.distinct(TestRecord.model_config_id)))
    )
    models_used = models_result.scalar() or 0

    return {
        "total_tests": row.total_tests or 0,
        "total_tokens_input": row.total_tokens_input or 0,
        "total_tokens_output": row.total_tokens_output or 0,
        "total_tokens": (row.total_tokens_input or 0) + (row.total_tokens_output or 0),
        "models_used": models_used,
        "avg_response_time_ms": round(row.avg_response_time_ms or 0, 1),
    }


async def get_usage_stats(
    db: AsyncSession,
    group_by: str = "model",
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """获取用量分布数据"""
    conditions = []
    if start_date:
        conditions.append(TestRecord.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        conditions.append(TestRecord.created_at <= datetime.fromisoformat(end_date + "T23:59:59"))

    if group_by == "model":
        return await _group_by_model(db, conditions)
    elif group_by in ("day", "week", "month"):
        return await _group_by_time(db, group_by, conditions)
    else:
        return {"group_by": group_by, "data": []}


async def _group_by_model(db, conditions):
    """按模型分组统计"""
    query = (
        select(
            ModelConfig.name.label("label"),
            func.count(TestRecord.id).label("test_count"),
            func.coalesce(func.sum(TestRecord.token_input), 0).label("token_input"),
            func.coalesce(func.sum(TestRecord.token_output), 0).label("token_output"),
            func.coalesce(func.avg(TestRecord.response_time_ms), 0).label("avg_response_time_ms"),
        )
        .join(ModelConfig, TestRecord.model_config_id == ModelConfig.id)
        .group_by(ModelConfig.name)
    )

    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    rows = result.all()

    return {
        "group_by": "model",
        "data": [
            {
                "label": r.label,
                "test_count": r.test_count,
                "token_input": r.token_input,
                "token_output": r.token_output,
                "avg_response_time_ms": round(r.avg_response_time_ms, 1),
            }
            for r in rows
        ],
    }


async def _group_by_time(db, period, conditions):
    """按时间分组统计（简化版 - 使用 created_at 的日期部分）"""
    # SQLite 使用 date() 函数
    if period == "day":
        date_expr = func.date(TestRecord.created_at)
    elif period == "week":
        # SQLite: 使用 strftime 获取周
        date_expr = func.strftime("%Y-W%W", TestRecord.created_at)
    else:  # month
        date_expr = func.strftime("%Y-%m", TestRecord.created_at)

    query = (
        select(
            date_expr.label("label"),
            func.count(TestRecord.id).label("test_count"),
            func.coalesce(func.sum(TestRecord.token_input), 0).label("token_input"),
            func.coalesce(func.sum(TestRecord.token_output), 0).label("token_output"),
            func.coalesce(func.avg(TestRecord.response_time_ms), 0).label("avg_response_time_ms"),
        )
        .group_by("label")
        .order_by("label")
    )

    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    rows = result.all()

    return {
        "group_by": period,
        "data": [
            {
                "label": r.label or "",
                "test_count": r.test_count,
                "token_input": r.token_input,
                "token_output": r.token_output,
                "avg_response_time_ms": round(r.avg_response_time_ms, 1),
            }
            for r in rows
        ],
    }
