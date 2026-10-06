"""Pruebas de integración para la dependencia de autenticación por API Key."""

from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from infrastructure.api.exceptions import register_api_exception_handlers
from infrastructure.api.security import get_valid_api_key
from shared.infrastructure.config.settings import settings


@pytest.fixture
def api_key_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "api_key", "test-api-key")
    app = FastAPI()
    register_api_exception_handlers(app)

    @app.get("/protected")
    def protected_route(
        _api_key: Annotated[None, Depends(get_valid_api_key)],
    ) -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def test_api_key_dependency_accepts_configured_key(api_key_client: TestClient) -> None:
    response = api_key_client.get("/protected", headers={"X-API-Key": "test-api-key"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong-key"}])
def test_api_key_dependency_rejects_missing_or_invalid_key(
    api_key_client: TestClient,
    headers: dict[str, str],
) -> None:
    response = api_key_client.get("/protected", headers=headers)

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Forbidden",
        "status": 403,
        "detail": "Falta una API Key válida.",
        "instance": "/protected",
        "code": "invalid_api_key",
    }
