"""Pruebas unitarias de la traducción de excepciones de dominio a HTTP."""

from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from domain.exceptions.auth_exceptions import AuthException, InvalidCredentialsException
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
    assert response.json() == {"error": {"code": "not_found", "message": "No encontrado"}}


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
    assert response.json() == {
        "error": {"code": expected_code, "message": str(exception)}
    }


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
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Error interno del servidor.",
        }
    }


def test_auth_exceptions_are_domain_exceptions() -> None:
    assert issubclass(AuthException, DomainException)


def test_invalid_credentials_exception_is_mapped_to_401() -> None:
    client = TestClient(
        _app_raising(InvalidCredentialsException(), register_api_exception_handlers)
    )

    response = client.get("/error")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {
            "code": "invalid_credentials",
            "message": "Invalid username or password",
        }
    }
