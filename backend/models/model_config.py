"""ModelConfig ORM 模型：可用模型及其参数配置"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel, utcnow


class ModelConfig(BaseModel):
    """模型配置表"""
    __tablename__ = "model_configs"
    __table_args__ = (
        UniqueConstraint("model_id", "provider", name="uq_model_provider"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模型显示名称")
    model_id: Mapped[str] = mapped_column(String(200), nullable=False, comment="API 模型标识符")
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="aliyun", comment="服务商标识")
    api_endpoint: Mapped[str] = mapped_column(String(500), nullable=False, comment="API 端点 URL")
    default_params: Mapped[dict] = mapped_column(JSON, default=dict, comment="默认参数")
    supported_modalities: Mapped[list] = mapped_column(JSON, nullable=False, comment="支持的输入模态列表")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    # 关系
    test_records = relationship("TestRecord", back_populates="model_config")
    comparison_groups = relationship("ComparisonGroup", back_populates="model_config")
