"""Fixtures compartidas: base SQLite en memoria y cliente HTTP de la app real."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Los modelos deben estar importados para que ``Base.metadata`` los conozca
# antes de crear el esquema de la base en memoria.
from infrastructure.database.models.product_orm import ProductORM  # noqa: F401
from infrastructure.database.models.role_orm import RoleORM  # noqa: F401
from infrastructure.database.models.user_orm import UserORM  # noqa: F401
from main import app
from shared.infrastructure.config.settings import settings
from shared.infrastructure.persistence.database import Base, get_db


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    """Motor SQLite en memoria con el esquema completo creado."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    """Fábrica de sesiones contra la base en memoria de la prueba."""
    return sessionmaker(bind=engine)


@pytest.fixture
def client(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Cliente HTTP con ``get_db`` apuntando a la base en memoria."""
    monkeypatch.setattr(settings, "jwt_secret_key", "clave-de-prueba")

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
