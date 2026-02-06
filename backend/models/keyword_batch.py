"""KeywordBatch ORM 模型：关键词批量测试任务"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel


class BatchStatus(str, enum.Enum):
    """批量任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class KeywordBatch(BaseModel):
    """关键词批次表"""
    __tablename__ = "keyword_batches"
    __table_args__ = (
        Index("ix_keyword_batches_created_at", "created_at"),
    )

    model_config_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("model_configs.id"),
        nullable=False,
        comment="使用的模型配置",
    )
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, comment="关键词列表")
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False, comment="提示词模板")
    custom_params: Mapped[dict] = mapped_column(JSON, default=dict, comment="自定义模型参数")
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, comment="关键词总数")
    completed_count: Mapped[int] = mapped_column(Integer, default=0, comment="已完成数")
    failed_count: Mapped[int] = mapped_column(Integer, default=0, comment="失败数")
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, native_enum=False, length=15),
        nullable=False,
        default=BatchStatus.PENDING,
        comment="状态",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )

    # 关系
    test_records = relationship("TestRecord", back_populates="keyword_batch")
