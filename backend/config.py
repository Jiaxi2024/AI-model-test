"""配置管理模块：加载环境变量和定义常量"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# 数据库配置
DATABASE_DIR = BASE_DIR / "data"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_DIR / 'eval.db'}"

# 文件上传配置
UPLOAD_DIR = BASE_DIR / "uploads"

# 文件大小限制（字节）
MAX_IMAGE_SIZE = 10 * 1024 * 1024       # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024      # 100MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024       # 25MB

# 支持的文件格式
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm"}
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"}

# 模态对应的文件大小限制
FILE_SIZE_LIMITS = {
    "image": MAX_IMAGE_SIZE,
    "video": MAX_VIDEO_SIZE,
    "audio": MAX_AUDIO_SIZE,
}

# 所有支持的 MIME 类型及其模态
MIME_TO_MODALITY = {}
for mime in ALLOWED_IMAGE_TYPES:
    MIME_TO_MODALITY[mime] = "image"
for mime in ALLOWED_VIDEO_TYPES:
    MIME_TO_MODALITY[mime] = "video"
for mime in ALLOWED_AUDIO_TYPES:
    MIME_TO_MODALITY[mime] = "audio"

# 阿里云 API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 模型 API 超时（秒）
MODEL_API_TIMEOUT = 60

# AI 自动补全配置
AUTOCOMPLETE_MODEL = os.getenv("AUTOCOMPLETE_MODEL", "qwen-turbo")
AUTOCOMPLETE_MAX_TOKENS = 100

# 前端静态文件目录
FRONTEND_DIR = BASE_DIR / "frontend"
