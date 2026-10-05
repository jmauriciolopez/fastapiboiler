"""Manejadores HTTP propios del API, sobre los genéricos compartidos."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from domain.exceptions.auth_exceptions import (
    AuthException,
    InvalidAPIKeyException,
    InvalidTokenException,
)
from shared.infrastructure.exceptions import register_exception_handlers
from shared.infrastructure.problem_details import problem_response


def register_api_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores compartidos y los específicos de este API."""
    register_exception_handlers(app)

    @app.exception_handler(AuthException)
    def auth_exception_handler(request: Request, exc: AuthException) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidTokenException)
    def invalid_token_handler(request: Request, exc: InvalidTokenException) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidAPIKeyException)
    def invalid_api_key_handler(
        request: Request,
        _exc: InvalidAPIKeyException,
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="invalid_api_key",
            detail="Falta una API Key válida.",
        )
