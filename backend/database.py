"""数据库连接、会话管理、初始化"""

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import DATABASE_URL, DATABASE_DIR
from backend.models.base import Base

# 异步引擎 — 设置 connect_args 增加 SQLite 锁超时时间
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"timeout": 30},  # SQLite busy_timeout = 30 秒
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """为每个新 SQLite 连接启用 WAL 模式和优化配置"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")      # 允许并发读写
    cursor.execute("PRAGMA synchronous=NORMAL")     # 平衡性能与安全
    cursor.execute("PRAGMA busy_timeout=30000")     # 30 秒锁等待
    cursor.close()

# 异步会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """依赖注入：获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """初始化数据库：创建所有表并填充种子数据"""
    # 确保数据目录存在
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # 导入所有模型以确保 Base.metadata 包含所有表
    import backend.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 填充种子数据
    await _seed_models()


async def _seed_models():
    """预置阿里云 Qwen 系列模型配置"""
    from backend.models.model_config import ModelConfig

    seed_models = [
        {
            "name": "Qwen-Omni-Turbo",
            "model_id": "qwen-omni-turbo",
            "provider": "aliyun",
            "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_params": {"temperature": 0.7, "max_tokens": 2048},
            "supported_modalities": ["text", "image", "audio", "video"],
            "is_active": True,
        },
        {
            "name": "Qwen-Plus",
            "model_id": "qwen-plus",
            "provider": "aliyun",
            "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_params": {"temperature": 0.7, "max_tokens": 2048},
            "supported_modalities": ["text", "image"],
            "is_active": True,
        },
        {
            "name": "Qwen-Turbo",
            "model_id": "qwen-turbo",
            "provider": "aliyun",
            "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_params": {"temperature": 0.7, "max_tokens": 2048},
            "supported_modalities": ["text"],
            "is_active": True,
        },
        {
            "name": "Qwen-Max",
            "model_id": "qwen-max",
            "provider": "aliyun",
            "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_params": {"temperature": 0.7, "max_tokens": 4096},
            "supported_modalities": ["text", "image"],
            "is_active": True,
        },
        {
            "name": "Qwen-VL-Plus",
            "model_id": "qwen-vl-plus",
            "provider": "aliyun",
            "api_endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_params": {"temperature": 0.7, "max_tokens": 2048},
            "supported_modalities": ["text", "image", "video"],
            "is_active": True,
        },
    ]

    async with async_session() as session:
        from sqlalchemy import select

        # 检查是否已有种子数据
        result = await session.execute(select(ModelConfig).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # 已有数据，跳过

        for model_data in seed_models:
            model = ModelConfig(**model_data)
            session.add(model)

        await session.commit()
