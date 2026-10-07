from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.infrastructure.config.settings import settings
from shared.infrastructure.persistence.base import Base

__all__ = ["Base"]

logger = logging.getLogger(__name__)


def normalize_database_url(database_url: str) -> str:
    """Ensure the URL uses an async-compatible driver.

    * ``postgresql`` / ``postgres``  → ``postgresql+psycopg``
    * ``sqlite``                     → ``sqlite+aiosqlite``
    * Anything already suffixed is left untouched.
    """
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername == "sqlite":
        url = url.set(drivername="sqlite+aiosqlite")
    return url.render_as_string(hide_password=False)


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL debe configurarse para usar la base de datos.")

    return create_async_engine(
        normalize_database_url(settings.database_url),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=settings.db_pool_recycle,
        pool_timeout=settings.db_pool_timeout,
        echo=settings.db_echo,
        future=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,  # never re-query after commit inside a request
        class_=AsyncSession,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one async session per request."""
    async with get_session_factory()() as session:
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Database error — rollback executed")
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """For background workers, CLI tasks, or code outside FastAPI."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
