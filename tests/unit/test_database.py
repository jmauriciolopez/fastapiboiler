"""Pruebas unitarias de la configuración de acceso a la base de datos."""

import pytest

from shared.infrastructure.database import get_db, normalize_database_url


def test_database_dependency_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        next(get_db())


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_postgresql_urls_use_psycopg_driver(scheme: str) -> None:
    normalized_url = normalize_database_url(f"{scheme}://user:password@localhost:5432/demo")

    assert normalized_url.startswith("postgresql+psycopg://")


def test_non_postgresql_urls_are_left_untouched() -> None:
    assert normalize_database_url("sqlite:///./app.db") == "sqlite:///./app.db"
