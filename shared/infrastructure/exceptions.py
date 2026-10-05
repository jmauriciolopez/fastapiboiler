import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shared.domain.exceptions import (
    DomainConflictException,
    DomainException,
    DomainValidationException,
    EntityNotFoundException,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    def domain_error_handler(
        _request: Request,
        exc: DomainException,
        *,
        status_code: int,
        code: str,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": code, "message": exc.message}},
        )

    @app.exception_handler(EntityNotFoundException)
    def entity_not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
        return domain_error_handler(
            request,
            exc,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
        )

    @app.exception_handler(DomainValidationException)
    def domain_validation_handler(request: Request, exc: DomainValidationException) -> JSONResponse:
        return domain_error_handler(
            request,
            exc,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="domain_validation_error",
        )

    @app.exception_handler(DomainConflictException)
    def domain_conflict_handler(request: Request, exc: DomainConflictException) -> JSONResponse:
        return domain_error_handler(
            request,
            exc,
            status_code=status.HTTP_409_CONFLICT,
            code="conflict",
        )

    @app.exception_handler(DomainException)
    def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return domain_error_handler(
            request,
            exc,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="domain_error",
        )

    @app.exception_handler(Exception)
    def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Error interno del servidor.",
                }
            },
        )
