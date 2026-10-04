from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shared.domain.exceptions import DomainException, EntityNotFoundException

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EntityNotFoundException)
    def entity_not_found_handler(_request: Request, exc: EntityNotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message}
        )
