"""历史记录 CRUD 服务"""

from datetime import datetime

from sqlalchemy import select, func, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import TestRecord, TestInput, ModelConfig, UploadedFile, RecordStatus


async def list_history(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    model_id: str | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
) -> dict:
    """分页查询历史记录"""
    query = select(TestRecord).options(
        selectinload(TestRecord.model_config),
        selectinload(TestRecord.test_input).selectinload(TestInput.uploaded_files),
    )

    conditions = []
    if model_id:
        conditions.append(TestRecord.model_config_id == model_id)
    if status:
        conditions.append(TestRecord.status == status)
    if keyword:
        conditions.append(or_(
            TestRecord.prompt_text.ilike(f"%{keyword}%"),
            TestRecord.output_text.ilike(f"%{keyword}%"),
        ))
    if start_date:
        conditions.append(TestRecord.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        conditions.append(TestRecord.created_at <= datetime.fromisoformat(end_date + "T23:59:59"))

    if conditions:
        query = query.where(and_(*conditions))

    # 总数
    count_query = select(func.count(TestRecord.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(TestRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    records = result.scalars().unique().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": [_format_record_summary(r) for r in records],
    }


async def get_record_detail(db: AsyncSession, record_id: str) -> dict | None:
    """获取单条历史记录详情"""
    result = await db.execute(
        select(TestRecord)
        .options(
            selectinload(TestRecord.model_config),
            selectinload(TestRecord.test_input).selectinload(TestInput.uploaded_files),
        )
        .where(TestRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        return None
    return _format_record_detail(record)


async def delete_record(db: AsyncSession, record_id: str) -> bool:
    """删除单条历史记录"""
    result = await db.execute(
        select(TestRecord).where(TestRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        return False
    await db.delete(record)
    return True


async def batch_delete_records(
    db: AsyncSession,
    record_ids: list[str] | None = None,
    delete_all: bool = False,
) -> int:
    """批量删除历史记录"""
    if delete_all:
        result = await db.execute(delete(TestRecord))
        return result.rowcount
    elif record_ids:
        result = await db.execute(
            delete(TestRecord).where(TestRecord.id.in_(record_ids))
        )
        return result.rowcount
    return 0


def _format_record_summary(record: TestRecord) -> dict:
    """格式化记录摘要"""
    modalities = set(["text"])
    if record.test_input and record.test_input.uploaded_files:
        for f in record.test_input.uploaded_files:
            mod = f.modality.value if hasattr(f.modality, 'value') else f.modality
            modalities.add(mod)

    input_text = record.prompt_text or (record.test_input.text_content if record.test_input else "")
    return {
        "id": record.id,
        "model_name": record.model_config.name if record.model_config else "未知",
        "input_summary": (input_text or "")[:100],
        "output_summary": (record.output_text or "")[:100],
        "modalities": list(modalities),
        "token_total": (record.token_input or 0) + (record.token_output or 0),
        "response_time_ms": record.response_time_ms,
        "status": record.status.value if hasattr(record.status, 'value') else record.status,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def _format_record_detail(record: TestRecord) -> dict:
    """格式化记录详情"""
    files = []
    if record.test_input and record.test_input.uploaded_files:
        for f in record.test_input.uploaded_files:
            files.append({
                "id": f.id,
                "file_name": f.file_name,
                "file_size": f.file_size,
                "mime_type": f.mime_type,
                "modality": f.modality.value if hasattr(f.modality, 'value') else f.modality,
                "preview_url": f"/uploads/{f.file_path.replace(chr(92), '/')}",
            })

    return {
        "id": record.id,
        "model": {
            "id": record.model_config.id,
            "name": record.model_config.name,
            "model_id": record.model_config.model_id,
        } if record.model_config else None,
        "input": {
            "text": record.prompt_text or (record.test_input.text_content if record.test_input else None),
            "files": files,
        },
        "output_text": record.output_text,
        "output_audio_url": f"/uploads/{record.output_audio_path.replace(chr(92), '/')}" if record.output_audio_path else None,
        "params": record.custom_params,
        "token_input": record.token_input,
        "token_output": record.token_output,
        "response_time_ms": record.response_time_ms,
        "status": record.status.value if hasattr(record.status, 'value') else record.status,
        "error_message": record.error_message,
        "raw_response": record.raw_response,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
