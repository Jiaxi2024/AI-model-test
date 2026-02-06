"""文件上传/校验/存储服务"""

import base64
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile, HTTPException

from backend.config import (
    UPLOAD_DIR,
    MIME_TO_MODALITY,
    FILE_SIZE_LIMITS,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_VIDEO_TYPES,
    ALLOWED_AUDIO_TYPES,
)


def validate_file(file: UploadFile) -> tuple[str, str]:
    """
    校验上传文件的格式和大小。

    Args:
        file: 上传的文件对象

    Returns:
        (modality, mime_type) 元组

    Raises:
        HTTPException: 格式或大小不符合要求
    """
    # 检查 MIME 类型
    mime_type = file.content_type or ""
    if mime_type not in MIME_TO_MODALITY:
        all_types = sorted(ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES)
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {mime_type}。支持的格式: {', '.join(all_types)}",
        )

    modality = MIME_TO_MODALITY[mime_type]
    return modality, mime_type


async def validate_file_size(file: UploadFile, modality: str) -> int:
    """
    校验文件大小。

    Args:
        file: 上传的文件对象
        modality: 模态类型

    Returns:
        文件大小（字节）

    Raises:
        HTTPException: 文件超过大小限制
    """
    # 读取文件获取大小
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # 重置文件指针

    max_size = FILE_SIZE_LIMITS.get(modality, 10 * 1024 * 1024)
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"{modality} 文件大小超过限制: {actual_mb:.1f}MB > {max_mb:.0f}MB",
        )

    return file_size


async def save_file(file: UploadFile, modality: str) -> tuple[str, str, int]:
    """
    保存上传的文件到本地存储。

    Args:
        file: 上传的文件对象
        modality: 模态类型

    Returns:
        (存储路径, 原始文件名, 文件大小) 元组
    """
    # 确保上传目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 按日期和模态组织子目录
    today = datetime.now().strftime("%Y%m%d")
    sub_dir = UPLOAD_DIR / today / modality
    sub_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    original_name = file.filename or "unnamed"
    ext = Path(original_name).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = sub_dir / unique_name

    # 读取并保存文件
    content = await file.read()
    file_size = len(content)

    with open(file_path, "wb") as f:
        f.write(content)

    # 返回相对于 UPLOAD_DIR 的路径
    relative_path = str(file_path.relative_to(UPLOAD_DIR))
    return relative_path, original_name, file_size


def get_file_url(file_path: str) -> str:
    """
    获取文件的浏览器访问 URL（用于前端预览）。

    Args:
        file_path: 相对于 uploads/ 的文件路径

    Returns:
        文件的 HTTP 访问 URL
    """
    # 统一使用正斜杠
    normalized_path = file_path.replace("\\", "/")
    return f"/uploads/{normalized_path}"


def get_file_base64_url(file_path: str, mime_type: str) -> str:
    """
    将本地文件转为 base64 data URL，用于发送给模型 API。

    阿里云 DashScope OpenAI 兼容接口要求：
    - 图片: data:image/png;base64,xxx （包含 MIME 类型）
    - 音频/视频: data:;base64,xxx （不包含 MIME 类型）

    Args:
        file_path: 相对于 uploads/ 的文件路径
        mime_type: 文件的 MIME 类型

    Returns:
        base64 data URL
    """
    abs_path = UPLOAD_DIR / file_path
    with open(abs_path, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("ascii")

    # DashScope 图片需要完整 MIME 前缀，音频/视频用 data:;base64
    if mime_type.startswith("image/"):
        return f"data:{mime_type};base64,{b64}"
    else:
        return f"data:;base64,{b64}"
