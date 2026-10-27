"""
Async SQLAlchemy database engine, session factory, and dependency injection.
Uses asyncpg driver for full async PostgreSQL support.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.utils.logger import logger


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
is_sqlite = settings.ASYNC_DATABASE_URL.startswith("sqlite")
engine_options = {
    "echo": settings.ENVIRONMENT == "development",
}
if not is_sqlite:
    engine_options.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
    })

engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    **engine_options,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.
    Automatically rolls back on exception and always closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
async def create_all_tables() -> None:
    """Create all database tables (used at startup in development)."""
    async with engine.begin() as conn:
        # Import all models so Base.metadata is populated
        from app.models import defect, project, test_case, test_result, test_run  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created / verified.")


async def dispose_engine() -> None:
    """Gracefully close all engine connections (called at shutdown)."""
    await engine.dispose()
    logger.info("Database engine disposed.")


# Aliases for lifespan hooks in main.py
init_db = create_all_tables
close_db = dispose_engine
