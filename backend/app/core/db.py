from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
_engine_options: dict = {"pool_pre_ping": True}
if settings.app_env == "test":
    # Tests use a fresh event loop per test. A pooled asyncpg connection
    # cannot move to the next loop.
    _engine_options["poolclass"] = NullPool
else:
    _engine_options["pool_size"] = 5
    _engine_options["max_overflow"] = 10

engine = create_async_engine(settings.database_url, **_engine_options)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
