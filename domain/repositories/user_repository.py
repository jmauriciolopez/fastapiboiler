from typing import Protocol
from uuid import UUID

from domain.entities.role import Role
from domain.entities.user import User
from shared.domain.repository_port import RepositoryPort


class UserRepositoryPort(RepositoryPort[User], Protocol):
    def get_active_roles(self, role_ids: list[UUID]) -> list[Role]: ...
    
    def get_by_username(self, username: str) -> User | None: ...
