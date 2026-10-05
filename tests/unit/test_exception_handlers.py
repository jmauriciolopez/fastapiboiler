"""Pruebas unitarias de la traducción de excepciones de dominio a HTTP."""

from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from domain.exceptions.auth_exceptions import (
    AuthException,
    InvalidAPIKeyException,
    InvalidCredentialsException,
)
from infrastructure.api.exceptions import register_api_exception_handlers
from shared.domain.exceptions import (
    DomainConflictException,
    DomainException,
    DomainValidationException,
    EntityNotFoundException,
)
from shared.infrastructure.exceptions import register_exception_handlers


def _app_raising(
    exception: Exception,
    register: Callable[[FastAPI], None] = register_exception_handlers,
) -> FastAPI:
    exception_app = FastAPI()
    register(exception_app)

    @exception_app.get("/error")
    def raise_exception() -> None:
        raise exception

    return exception_app


def test_domain_not_found_exception_is_mapped_to_404() -> None:
    response = TestClient(_app_raising(EntityNotFoundException("No encontrado"))).get("/error")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "No encontrado",
        "instance": "/error",
        "code": "not_found",
    }


@pytest.mark.parametrize(
    ("exception", "expected_status", "expected_code"),
    [
        (DomainValidationException("Regla inválida"), 422, "domain_validation_error"),
        (DomainConflictException("Conflicto"), 409, "conflict"),
    ],
)
def test_domain_errors_are_mapped_to_consistent_http_responses(
    exception: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    response = TestClient(_app_raising(exception)).get("/error")

    assert response.status_code == expected_status
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == expected_status
    assert response.json()["code"] == expected_code
    assert response.json()["detail"] == str(exception)


def test_unmapped_integrity_error_is_returned_as_json_500() -> None:
    integrity_error = IntegrityError(
        "INSERT INTO users",
        {},
        Exception("FOREIGN KEY constraint failed"),
    )
    client = TestClient(
        _app_raising(integrity_error),
        raise_server_exceptions=False,
    )

    response = client.get("/error")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 500
    assert response.json()["code"] == "internal_error"
    assert response.json()["detail"] == "Error interno del servidor."


def test_auth_exceptions_are_domain_exceptions() -> None:
    assert issubclass(AuthException, DomainException)


def test_invalid_credentials_exception_is_mapped_to_401() -> None:
    client = TestClient(
        _app_raising(InvalidCredentialsException(), register_api_exception_handlers)
    )

    response = client.get("/error")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 401
    assert response.json()["code"] == "invalid_credentials"
    assert response.json()["detail"] == "Invalid username or password"


def test_api_key_error_uses_problem_details() -> None:
    client = TestClient(
        _app_raising(InvalidAPIKeyException(), register_api_exception_handlers)
    )

    response = client.get("/error")

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "invalid_api_key"


def test_http_exception_uses_problem_details_and_preserves_headers() -> None:
    from fastapi import HTTPException

    client = TestClient(
        _app_raising(
            HTTPException(status_code=418, detail="No disponible", headers={"X-Test": "yes"})
        )
    )

    response = client.get("/error")

    assert response.status_code == 418
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["x-test"] == "yes"
    assert response.json()["code"] == "http_error"


def test_request_validation_error_uses_problem_details() -> None:
    validation_app = FastAPI()
    register_exception_handlers(validation_app)

    @validation_app.get("/items/{item_id}")
    def read_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    response = TestClient(validation_app).get("/items/not-an-int")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "request_validation_error"
    assert response.json()["errors"][0]["loc"] == ["path", "item_id"]
