"""ComparisonSession + ComparisonGroup ORM 模型：对比测试会话"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel


class ComparisonStatus(str, enum.Enum):
    """对比会话状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ComparisonSession(BaseModel):
    """对比会话表"""
    __tablename__ = "comparison_sessions"

    test_input_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_inputs.id"),
        nullable=False,
        comment="共用的输入内容",
    )
    status: Mapped[ComparisonStatus] = mapped_column(
        Enum(ComparisonStatus, native_enum=False, length=15),
        nullable=False,
        default=ComparisonStatus.PENDING,
        comment="状态",
    )

    # 关系
    test_input = relationship("TestInput", back_populates="comparison_sessions")
    groups = relationship("ComparisonGroup", back_populates="comparison_session", cascade="all, delete-orphan")
    test_records = relationship("TestRecord", back_populates="comparison_session")


class ComparisonGroup(BaseModel):
    """对比组表"""
    __tablename__ = "comparison_groups"
    __table_args__ = (
        UniqueConstraint("comparison_session_id", "group_index", name="uq_session_group_index"),
    )

    comparison_session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("comparison_sessions.id"),
        nullable=False,
        comment="所属对比会话",
    )
    model_config_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("model_configs.id"),
        nullable=False,
        comment="使用的模型配置",
    )
    custom_params: Mapped[dict] = mapped_column(JSON, default=dict, comment="本组自定义参数")
    group_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="组序号（0=左，1=右）",
    )
    test_record_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("test_records.id"),
        nullable=True,
        comment="关联的测试记录",
    )

    # 关系
    comparison_session = relationship("ComparisonSession", back_populates="groups")
    model_config = relationship("ModelConfig", back_populates="comparison_groups")
    test_record = relationship("TestRecord", foreign_keys=[test_record_id])
