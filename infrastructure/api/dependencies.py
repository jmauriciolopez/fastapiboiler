"""Composition root: construye servicios y adaptadores por solicitud."""

import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from application.ports.logger import LoggerPort
from application.ports.password_hasher import PasswordHasher
from application.ports.token_service import TokenServicePort
from application.services.auth_service import AuthService
from application.services.role_service import RoleService
from application.services.user_service import UserService
from domain.repositories.user_repository import UserRepositoryPort
from infrastructure.database.repositories.role_repository import RoleRepository
from infrastructure.database.repositories.user_repository import UserRepository
from infrastructure.logging.std_logger import StdLogger
from infrastructure.security.password_hasher import Argon2PasswordHasher
from infrastructure.security.token_service import JwtTokenService
from shared.infrastructure.database import get_db


def get_logger() -> LoggerPort:
    return StdLogger(name="HexagonalApp")


def get_role_service(
    db: Annotated[Session, Depends(get_db)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> RoleService:
    return RoleService(RoleRepository(db), logger)


def get_user_repository(db: Annotated[Session, Depends(get_db)]) -> UserRepositoryPort:
    return UserRepository(db)


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service() -> TokenServicePort:
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY debe configurarse para emitir tokens.")
    return JwtTokenService(secret_key)


def get_user_service(
    repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> UserService:
    return UserService(repository, password_hasher, logger)


def get_auth_service(
    repository: Annotated[UserRepositoryPort, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenServicePort, Depends(get_token_service)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> AuthService:
    return AuthService(repository, password_hasher, token_service, logger)
