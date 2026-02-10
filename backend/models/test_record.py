"""TestRecord ORM 模型：完整的模型推理交互记录"""

import enum

from sqlalchemy import Enum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel


class RecordStatus(str, enum.Enum):
    """测试记录状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TestRecord(BaseModel):
    """测试记录表"""
    __tablename__ = "test_records"
    __table_args__ = (
        Index("ix_test_records_created_at", "created_at"),
        Index("ix_test_records_model_config_id", "model_config_id", "created_at"),
        Index("ix_test_records_status", "status"),
        Index("ix_test_records_keyword_batch_id", "keyword_batch_id"),
        Index("ix_test_records_comparison_session_id", "comparison_session_id"),
    )

    model_config_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("model_configs.id"),
        nullable=False,
        comment="使用的模型配置",
    )
    test_input_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_inputs.id"),
        nullable=False,
        comment="关联的输入内容",
    )
    custom_params: Mapped[dict] = mapped_column(JSON, default=dict, comment="本次请求的自定义参数")
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完整提示词文本")
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模型返回的文本内容")
    output_audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="模型返回的音频文件路径")
    token_input: Mapped[int] = mapped_column(Integer, default=0, comment="输入 Token 消耗")
    token_output: Mapped[int] = mapped_column(Integer, default=0, comment="输出 Token 消耗")
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0, comment="响应耗时（毫秒）")
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, native_enum=False, length=10),
        nullable=False,
        default=RecordStatus.PENDING,
        comment="状态",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="失败时的错误信息")
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True, comment="模型原始返回（JSON 字符串，调试用）")
    keyword_batch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("keyword_batches.id"),
        nullable=True,
        comment="所属批量测试",
    )
    comparison_session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("comparison_sessions.id"),
        nullable=True,
        comment="所属对比会话",
    )

    # 关系
    model_config = relationship("ModelConfig", back_populates="test_records")
    test_input = relationship("TestInput", back_populates="test_records")
    keyword_batch = relationship("KeywordBatch", back_populates="test_records")
    comparison_session = relationship("ComparisonSession", back_populates="test_records")
