"""
Database engine and session management.
Uses SQLAlchemy 2.0 async — SQLite (dev) or PostgreSQL (production).

All table DDL is PostgreSQL-compatible — no SQLite-deadlocked syntax.
Migration strategy: SQLAlchemy create_all in dev, Alembic in production.
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ——— Async engine ———
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # PostgreSQL 兼容连接池参数 (对 SQLite 无害)
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖项 — 每次请求获取一个独立的异步数据库会话。"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    启动时自动检查并创建所有缺失的表 (幂等操作)。
    与 PostgreSQL 完全兼容 — 使用标准 DDL，不依赖 SQLite 特有语法。

    执行流程:
    1. 连接数据库
    2. 检查所有模型对应的表是否存在
    3. 不存在 → 自动 CREATE TABLE
    4. 已存在 → 跳过 (不丢数据)
    """
    try:
        async with engine.begin() as conn:
            # 先导入所有模型，确保它们注册到 Base.metadata
            from app.models.user import User, SavedPresentation, ChatHistory  # noqa: F401
            from app.models.task import Task  # noqa: F401

            # 输出检测结果
            existing = await conn.run_sync(
                lambda sync_conn: set(
                    sync_conn.dialect.get_table_names(sync_conn)  # type: ignore[arg-type]
                )
            )
            expected = set(Base.metadata.tables.keys())
            missing = expected - existing

            if missing:
                logger.info(f"检测到缺失数据表: {missing}，正在自动创建...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info(f"数据库初始化完成 — 新建表: {missing}")
            else:
                logger.info(f"数据库检查通过 — 所有 {len(expected)} 张表已存在")

            # 输出所有表名 (调试用)
            all_tables = await conn.run_sync(
                lambda sync_conn: list(sync_conn.dialect.get_table_names(sync_conn))  # type: ignore[arg-type]
            )
            logger.info(f"当前数据库表 ({len(all_tables)}): {', '.join(sorted(all_tables))}")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def check_database_health() -> dict:
    """
    数据库健康检查 — 供 /health 端点使用。
    返回表计数和连接状态。
    """
    try:
        async with async_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            await result.scalar()

            # 获取所有表
            from app.models.user import User  # noqa: F401
            from app.models.task import Task  # noqa: F401
            table_names = list(Base.metadata.tables.keys())

            return {
                "database": "connected",
                "tables": len(table_names),
                "table_names": sorted(table_names),
            }
    except Exception as e:
        return {"database": "error", "error": str(e)}
