"""TestInput ORM 模型：用户测试输入（文本 + 附件）"""

import enum

from sqlalchemy import Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel


class InputType(str, enum.Enum):
    """输入类型枚举"""
    SINGLE = "single"
    COMPARISON = "comparison"
    BATCH = "batch"


class TestInput(BaseModel):
    """测试输入表"""
    __tablename__ = "test_inputs"

    text_content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户输入的文本内容")
    input_type: Mapped[InputType] = mapped_column(
        Enum(InputType, native_enum=False, length=20),
        nullable=False,
        comment="输入类型",
    )

    # 关系
    uploaded_files = relationship("UploadedFile", back_populates="test_input", cascade="all, delete-orphan")
    test_records = relationship("TestRecord", back_populates="test_input")
    comparison_sessions = relationship("ComparisonSession", back_populates="test_input")
