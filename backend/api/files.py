"""文件上传 API 路由"""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.uploaded_file import UploadedFile as UploadedFileModel, FileModality
from backend.models.test_input import TestInput, InputType
from backend.services.file_manager import validate_file, validate_file_size, save_file, get_file_url

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传媒体文件（图片/视频/音频）"""
    # 校验格式
    modality, mime_type = validate_file(file)

    # 校验大小
    file_size = await validate_file_size(file, modality)

    # 保存文件
    file_path, original_name, file_size = await save_file(file, modality)

    # 创建临时 TestInput（后续推理时关联）
    test_input = TestInput(
        text_content=None,
        input_type=InputType.SINGLE,
    )
    db.add(test_input)
    await db.flush()

    # 保存文件记录到数据库
    uploaded_file = UploadedFileModel(
        test_input_id=test_input.id,
        file_name=original_name,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        modality=FileModality(modality),
    )
    db.add(uploaded_file)
    await db.flush()

    return {
        "id": uploaded_file.id,
        "file_name": original_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "modality": modality,
        "preview_url": get_file_url(file_path),
    }
