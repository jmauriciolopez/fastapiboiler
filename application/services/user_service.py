from typing import Any
from uuid import UUID

from application.ports.password_hasher import PasswordHasher
from domain.entities.user import User, UserStatus
from domain.repositories.user_repository import UserRepositoryPort
from shared.application.base_service import BaseService
from shared.application.ports.logger import LoggerPort
from shared.application.unit_of_work import UnitOfWork


class UserService(BaseService[User]):
    def __init__(
        self,
        repository: UserRepositoryPort,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        logger: LoggerPort,
    ) -> None:
        super().__init__(repository, uow, logger)
        self.user_repository = repository
        self.password_hasher = password_hasher

    async def create_user(
        self,
        *,
        username: str,
        email: str,
        phone: str,
        password: str,
        role_ids: list[UUID],
    ) -> User:
        # Roles and password hash run concurrently — both are I/O or CPU-bound.
        import asyncio

        roles, hashed = await asyncio.gather(
            self.user_repository.get_active_roles(role_ids),
            self.password_hasher.hash(password),
        )
        user = User(
            username=username,
            email=email,
            phone=phone,
            hashed_password=hashed,
            status=UserStatus.PENDING,
            roles=roles,
        )
        return await self.create(user)

    async def update_user(
        self,
        user_id: UUID,
        *,
        username: str,
        email: str,
        phone: str,
        status: UserStatus,
        role_ids: list[UUID],
        password: str | None,
    ) -> User:
        import asyncio

        current_user, roles = await asyncio.gather(
            self.get_by_id(user_id),
            self.user_repository.get_active_roles(role_ids),
        )
        hashed_password = (
            await self.password_hasher.hash(password)
            if password is not None
            else current_user.hashed_password
        )
        user = User(
            id=user_id,
            username=username,
            email=email,
            phone=phone,
            hashed_password=hashed_password,
            status=status,
            roles=roles,
            created_on=current_user.created_on,
            updated_on=current_user.updated_on,
            deleted=current_user.deleted,
        )
        return await self.update(user_id, user)

    async def patch_user(
        self,
        user_id: UUID,
        *,
        fields: dict[str, Any],
    ) -> User:
        """Apply a partial update.  Merges *fields* onto the current state.

        This is application logic — not HTTP logic — so it lives here rather
        than in the controller.
        """
        current = await self.get_by_id(user_id)
        return await self.update_user(
            user_id,
            username=fields.get("username", current.username),
            email=fields.get("email", current.email),
            phone=fields.get("phone", current.phone),
            status=fields.get("status", current.status),
            role_ids=fields.get("role_ids", [role.id for role in current.roles]),
            password=fields.get("password"),
        )
