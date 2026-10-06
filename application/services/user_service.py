from uuid import UUID

from application.ports.logger import LoggerPort
from application.ports.password_hasher import PasswordHasher
from domain.entities.user import User, UserStatus
from domain.repositories.user_repository import UserRepositoryPort
from shared.application.base_service import BaseService


class UserService(BaseService[User]):
    def __init__(self, repository: UserRepositoryPort, password_hasher: PasswordHasher, logger: LoggerPort) -> None:
        super().__init__(repository, logger)
        self.user_repository = repository
        self.password_hasher = password_hasher

    def create_user(
        self,
        *,
        username: str,
        email: str,
        phone: str,
        password: str,
        role_ids: list[UUID],
    ) -> User:
        user = User(
            username=username,
            email=email,
            phone=phone,
            hashed_password=self.password_hasher.hash(password),
            status=UserStatus.PENDING,
            roles=self.user_repository.get_active_roles(role_ids),
        )
        return self.create(user)

    def update_user(
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
        current_user = self.get_by_id(user_id)
        user = User(
            id=user_id,
            username=username,
            email=email,
            phone=phone,
            hashed_password=self.password_hasher.hash(password) if password is not None else current_user.hashed_password,
            status=status,
            roles=self.user_repository.get_active_roles(role_ids),
            created_on=current_user.created_on,
            updated_on=current_user.updated_on,
            deleted=current_user.deleted,
        )
        return self.update(user_id, user)
