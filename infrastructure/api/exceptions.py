"""Manejadores HTTP propios del API, sobre los genéricos compartidos."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from domain.exceptions.auth_exceptions import (
    AuthException,
    InvalidAPIKeyException,
    InvalidTokenException,
)
from shared.infrastructure.exceptions import register_exception_handlers


def register_api_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores compartidos y los específicos de este API."""
    register_exception_handlers(app)

    @app.exception_handler(AuthException)
    def auth_exception_handler(_request: Request, exc: AuthException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": {"code": "invalid_credentials", "message": exc.message}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidTokenException)
    def invalid_token_handler(_request: Request, exc: InvalidTokenException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": {"code": "invalid_token", "message": exc.message}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidAPIKeyException)
    def invalid_api_key_handler(_request: Request, _exc: InvalidAPIKeyException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "invalid_api_key",
                    "message": "Falta una API Key válida.",
                }
            },
        )
