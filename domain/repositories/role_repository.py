from typing import Protocol

from domain.entities.role import Role
from shared.domain.repository_port import RepositoryPort


class RoleRepositoryPort(RepositoryPort[Role], Protocol):
    pass
