import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from shared.domain.exceptions import (
    DomainConflictException,
    DomainException,
    DomainValidationException,
    EntityNotFoundException,
)
from shared.infrastructure.problem_details import problem_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    def domain_error_handler(
        request: Request,
        exc: DomainException,
        *,
        status_code: int,
        code: str,
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=status_code,
            code=code,
            detail=exc.message,
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

    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "La solicitud no pudo procesarse."
        return problem_response(
            request,
            status_code=exc.status_code,
            code="http_error",
            detail=detail,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "loc": error["loc"],
                "msg": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return problem_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="request_validation_error",
            detail="La solicitud contiene datos inválidos.",
            extensions={"errors": errors},
        )

    @app.exception_handler(Exception)
    def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return problem_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            detail="Error interno del servidor.",
        )
