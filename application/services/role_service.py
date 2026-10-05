from domain.entities.role import Role
from domain.repositories.role_repository import RoleRepositoryPort
from shared.application.base_service import BaseService


class RoleService(BaseService[Role]):
    def __init__(self, repository: RoleRepositoryPort) -> None:
        super().__init__(repository)
