"""
统一多模态模型评测平台 - 入口文件
运行方式: python app.py
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from fastapi.responses import JSONResponse
from fastapi import Request

from backend.config import HOST, PORT, DEBUG, FRONTEND_DIR, UPLOAD_DIR, DATABASE_DIR
from backend.database import init_db
from backend.api import api_router

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="统一多模态模型评测平台",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 全局错误处理中间件
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """捕获所有未处理的异常，返回统一 JSON 格式"""
        logger.error(f"未处理的异常: {request.method} {request.url} - {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试", "code": "INTERNAL_ERROR"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """处理参数校验错误"""
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": "VALIDATION_ERROR"},
        )

    # 注册 API 路由
    app.include_router(api_router, prefix="/api")

    # 挂载上传文件目录（供前端预览）
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # 挂载前端静态资源
    if FRONTEND_DIR.exists():
        app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
        app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
        app.mount(
            "/assets",
            StaticFiles(directory=str(FRONTEND_DIR / "assets")),
            name="assets",
        )

    # 前端 SPA 入口：所有非 /api 和非静态资源路径都返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """服务前端 SPA 页面"""
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app):
        """应用生命周期管理"""
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        await init_db()
        yield

    app.router.lifespan_context = lifespan

    return app


app = create_app()

if __name__ == "__main__":
    print(f"[*] 统一多模态模型评测平台启动中...")
    print(f"[*] 访问地址: http://localhost:{PORT}")
    print(f"[*] API 文档: http://localhost:{PORT}/docs")
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )
