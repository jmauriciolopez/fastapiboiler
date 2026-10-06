"""Dependencias de seguridad para las rutas protegidas por token."""

import hmac
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from application.ports.token_service import TokenServicePort
from domain.entities.user import User
from domain.exceptions.auth_exceptions import (
    InvalidAPIKeyException,
    InvalidTokenException,
)
from domain.repositories.user_repository import UserRepositoryPort
from infrastructure.api.dependencies import get_token_service, get_user_repository
from shared.infrastructure.config.settings import settings

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="JWT")
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="APIKey")


def get_valid_api_key(
    api_key: Annotated[str | None, Security(api_key_scheme)],
) -> None:
    """Valida el encabezado X-API-Key contra la clave configurada en API_KEY."""
    configured_api_key = settings.api_key
    if not configured_api_key:
        raise RuntimeError("API_KEY debe configurarse para usar la autenticación por API Key.")
    if api_key is None or not hmac.compare_digest(api_key, configured_api_key):
        raise InvalidAPIKeyException()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    token_service: Annotated[TokenServicePort, Depends(get_token_service)],
) -> User:
    """Resuelve el usuario autenticado a partir del token Bearer."""
    if credentials is None:
        raise InvalidTokenException("Falta el token de acceso.")

    claims = token_service.decode_token(credentials.credentials)
    username = claims.get("username")
    if not isinstance(username, str):
        raise InvalidTokenException("El token no identifica a un usuario.")

    user = repository.get_by_username(username)
    if user is None:
        raise InvalidTokenException("El usuario del token ya no está disponible.")
    return user
