from domain.entities.role import Role
from domain.repositories.role_repository import RoleRepositoryPort
from shared.application.base_service import BaseService
from shared.application.ports.logger import LoggerPort
from shared.application.unit_of_work import UnitOfWork


class RoleService(BaseService[Role]):
    def __init__(
        self,
        repository: RoleRepositoryPort,
        uow: UnitOfWork,
        logger: LoggerPort,
    ) -> None:
        super().__init__(repository, uow, logger)
