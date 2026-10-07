"""Shared fixtures: async SQLite in-memory DB and HTTP test client."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# ORM models must be imported so ``Base.metadata`` knows them before schema creation.
from infrastructure.database.models.product_orm import ProductORM  # noqa: F401
from infrastructure.database.models.role_orm import RoleORM  # noqa: F401
from infrastructure.database.models.user_orm import UserORM  # noqa: F401
from main import app
from shared.infrastructure.config.settings import settings
from shared.infrastructure.persistence.database import Base, get_db


@pytest.fixture(scope="function")
def engine() -> Generator[AsyncEngine, None, None]:
    """Async SQLite in-memory engine with the full schema created."""
    import asyncio

    _engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def _setup() -> None:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown() -> None:
        await _engine.dispose()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_setup())
    try:
        yield _engine
    finally:
        loop.run_until_complete(_teardown())
        loop.close()


@pytest.fixture(scope="function")
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Async session factory pointing at the test's in-memory DB."""
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="function")
def client(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """HTTP test client with ``get_db`` overridden to use the in-memory DB."""
    monkeypatch.setattr(settings, "jwt_secret_key", "clave-de-prueba-para-tests-con-longitud-suficiente")

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=True) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
