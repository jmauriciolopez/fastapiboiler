"""Pruebas unitarias de la configuración de acceso a la base de datos."""

import pytest

from scripts import create_tables
from shared.infrastructure.config.settings import settings
from shared.infrastructure.persistence.base import Base
from shared.infrastructure.persistence.database import get_db, normalize_database_url


def test_database_dependency_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", "")

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        next(get_db())


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_postgresql_urls_use_psycopg_driver(scheme: str) -> None:
    normalized_url = normalize_database_url(f"{scheme}://user:password@localhost:5432/demo")

    assert normalized_url.startswith("postgresql+psycopg://")


def test_non_postgresql_urls_are_left_untouched() -> None:
    assert normalize_database_url("sqlite:///./app.db") == "sqlite:///./app.db"


def test_create_tables_uses_database_url_loaded_by_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[object] = []
    engine_config: list[tuple[str, bool]] = []
    disposed: list[bool] = []

    class FakeEngine:
        def dispose(self) -> None:
            disposed.append(True)

    def fake_create_engine(url: str, *, pool_pre_ping: bool) -> FakeEngine:
        engine_config.append((url, pool_pre_ping))
        return FakeEngine()

    monkeypatch.setattr(settings, "database_url", "sqlite:///./test.db")
    monkeypatch.setattr(create_tables, "create_engine", fake_create_engine)
    monkeypatch.setattr(
        Base.metadata,
        "create_all",
        lambda bind: created.append(bind),
    )

    create_tables.main()

    assert len(created) == 1
    assert isinstance(created[0], FakeEngine)
    assert engine_config == [("sqlite:///./test.db", True)]
    assert disposed == [True]
