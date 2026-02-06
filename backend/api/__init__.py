"""API 路由注册：将所有路由挂载到 FastAPI"""

from fastapi import APIRouter

from backend.api.files import router as files_router
from backend.api.models import router as models_router
from backend.api.inference import router as inference_router
from backend.api.autocomplete import router as autocomplete_router
from backend.api.comparison import router as comparison_router
from backend.api.batch import router as batch_router
from backend.api.history import router as history_router
from backend.api.statistics import router as statistics_router
from backend.api.settings import router as settings_router

api_router = APIRouter()

# 注册所有子路由
api_router.include_router(models_router)
api_router.include_router(files_router)
api_router.include_router(inference_router)
api_router.include_router(autocomplete_router)
api_router.include_router(comparison_router)
api_router.include_router(batch_router)
api_router.include_router(history_router)
api_router.include_router(statistics_router)
api_router.include_router(settings_router)
