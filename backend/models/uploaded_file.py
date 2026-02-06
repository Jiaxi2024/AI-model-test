"""UploadedFile ORM 模型：用户上传的媒体文件"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import BaseModel


class FileModality(str, enum.Enum):
    """文件模态类型枚举"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class UploadedFile(BaseModel):
    """上传文件表"""
    __tablename__ = "uploaded_files"

    test_input_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_inputs.id"),
        nullable=False,
        comment="所属输入",
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="服务端存储路径")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小（字节）")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="MIME 类型")
    modality: Mapped[FileModality] = mapped_column(
        Enum(FileModality, native_enum=False, length=10),
        nullable=False,
        comment="模态类型",
    )

    # 关系
    test_input = relationship("TestInput", back_populates="uploaded_files")
