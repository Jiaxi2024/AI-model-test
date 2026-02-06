"""ORM 基类：声明 Base + 通用字段 mixin"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """SQLAlchemy 声明基类"""
    pass


class TimestampMixin:
    """通用时间戳字段 mixin"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """带 UUID 主键和时间戳的抽象基类"""
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
