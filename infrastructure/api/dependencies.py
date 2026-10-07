"""Composition root — builds services and adapters per request.

Rules:
* ``get_logger`` is cached (singleton) — safe because StdLogger is stateless
  after construction and Python's logging module is thread/coroutine-safe.
* Every other dependency is request-scoped (no cache) so each request gets
  its own AsyncSession and, therefore, its own UnitOfWork / transaction.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.password_hasher import PasswordHasher
from application.ports.token_service import TokenServicePort
from application.services.auth_service import AuthService
from application.services.product_service import ProductService
from application.services.role_service import RoleService
from application.services.user_service import UserService
from domain.repositories.user_repository import UserRepositoryPort
from infrastructure.database.repositories.product_repository import ProductRepository
from infrastructure.database.repositories.role_repository import RoleRepository
from infrastructure.database.repositories.user_repository import UserRepository
from infrastructure.logging.std_logger import StdLogger
from infrastructure.security.password_hasher import Argon2PasswordHasher
from infrastructure.security.token_service import JwtTokenService
from shared.application.ports.logger import LoggerPort
from shared.application.unit_of_work import UnitOfWork
from shared.infrastructure.config.settings import settings
from shared.infrastructure.persistence.database import get_db


# ---------------------------------------------------------------------------
# Stateless singletons — constructed once for the lifetime of the process
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_logger() -> LoggerPort:
    """Singleton logger — avoids per-request allocation and handler races."""
    return StdLogger(name="HexagonalApp")


@lru_cache(maxsize=1)
def get_password_hasher() -> PasswordHasher:
    """Singleton — Argon2PasswordHasher holds no mutable state."""
    return Argon2PasswordHasher()


# ---------------------------------------------------------------------------
# Request-scoped dependencies
# ---------------------------------------------------------------------------

def get_uow(db: Annotated[AsyncSession, Depends(get_db)]) -> UnitOfWork:
    return UnitOfWork(db)


def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepositoryPort:
    return UserRepository(db)


def get_token_service() -> TokenServicePort:
    secret_key = settings.jwt_secret_key
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY debe configurarse para emitir tokens.")
    return JwtTokenService(secret_key)


def get_role_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> RoleService:
    uow = UnitOfWork(db)
    return RoleService(RoleRepository(db), uow, logger)


def get_product_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> ProductService:
    uow = UnitOfWork(db)
    return ProductService(ProductRepository(db), uow, logger)


def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> UserService:
    uow = UnitOfWork(db)
    return UserService(UserRepository(db), uow, password_hasher, logger)


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenServicePort, Depends(get_token_service)],
    logger: Annotated[LoggerPort, Depends(get_logger)],
) -> AuthService:
    return AuthService(UserRepository(db), password_hasher, token_service, logger)
