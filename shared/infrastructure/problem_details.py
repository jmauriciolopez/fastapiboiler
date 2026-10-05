"""Construcción de respuestas HTTP Problem Details (RFC 9457)."""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def problem_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    detail: str,
    headers: Mapping[str, str] | None = None,
    extensions: dict[str, Any] | None = None,
) -> JSONResponse:
    """Crea una respuesta RFC 9457 con el código estable de la API."""
    try:
        title = HTTPStatus(status_code).phrase
    except ValueError:
        title = "Error"

    content: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
    }
    if extensions:
        content.update(extensions)

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
        headers=headers,
        media_type="application/problem+json",
    )
