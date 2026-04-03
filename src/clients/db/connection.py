from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config.config import get_settings
from log.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


def _create_engine():
    settings = get_settings()
    kwargs: dict = {
        "echo": settings.debug,
    }
    # Connection pool settings only apply to non-SQLite engines
    if "sqlite" not in settings.db_driver:
        kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "pool_timeout": 30,
            }
        )
    return create_async_engine(settings.database_url, **kwargs)


engine = _create_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    logger.info("Database connection pool initialized")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database connection pool closed")
