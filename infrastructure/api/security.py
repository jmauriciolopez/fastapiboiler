"""Dependencias de seguridad para las rutas protegidas por token."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from application.ports.token_service import TokenServicePort
from domain.entities.user import User
from domain.exceptions.auth_exceptions import InvalidTokenException
from domain.repositories.user_repository import UserRepositoryPort
from infrastructure.api.dependencies import get_token_service, get_user_repository

bearer_scheme = HTTPBearer(auto_error=False)


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
