"""Unit tests for database configuration helpers."""

import pytest

from shared.infrastructure.config.settings import settings
from shared.infrastructure.persistence.database import normalize_database_url


def test_database_dependency_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from shared.infrastructure.persistence.database import get_engine
    get_engine.cache_clear()
    monkeypatch.setattr(settings, "database_url", "")

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_engine()

    get_engine.cache_clear()


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_postgresql_urls_use_psycopg_driver(scheme: str) -> None:
    normalized_url = normalize_database_url(f"{scheme}://user:password@localhost:5432/demo")

    assert normalized_url.startswith("postgresql+psycopg://")


def test_sqlite_urls_use_aiosqlite_driver() -> None:
    assert normalize_database_url("sqlite:///./app.db").startswith("sqlite+aiosqlite://")


def test_already_suffixed_urls_are_left_untouched() -> None:
    url = "postgresql+psycopg://user:pw@host/db"
    assert normalize_database_url(url) == url
