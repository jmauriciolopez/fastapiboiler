from typing import Generic, TypeVar
from uuid import UUID

from shared.application.ports.logger import LoggerPort
from shared.application.unit_of_work import UnitOfWork
from shared.domain.pagination import PaginatedResult
from shared.domain.repository_port import RepositoryPort

M = TypeVar("M")


class BaseService(Generic[M]):
    def __init__(
        self,
        repository: RepositoryPort[M],
        uow: UnitOfWork,
        logger: LoggerPort,
    ) -> None:
        self.repository = repository
        self.uow = uow
        self.logger = logger
        self._entity_name = self.__class__.__name__.replace("Service", "")

    async def create(self, entity: M) -> M:
        self.logger.debug(f"Creando nuevo {self._entity_name}")
        saved = await self.repository.save(entity)
        await self.uow.commit()
        self.logger.info(f"{self._entity_name} creado exitosamente")
        return saved

    async def get_by_id(self, entity_id: int | UUID) -> M:
        self.logger.debug(f"Buscando {self._entity_name} por ID: {entity_id}")
        return await self.repository.get_by_id(entity_id)

    async def list_all(self) -> list[M]:
        self.logger.debug(f"Listando todos los {self._entity_name}")
        return await self.repository.get_all()

    async def list_page(self, limit: int, offset: int) -> PaginatedResult[M]:
        self.logger.debug(
            f"Listando {self._entity_name} (página limit={limit}, offset={offset})"
        )
        return await self.repository.get_page(limit=limit, offset=offset)

    async def update(self, entity_id: int | UUID, entity: M) -> M:
        self.logger.debug(f"Actualizando {self._entity_name} ID: {entity_id}")
        updated = await self.repository.update(entity_id=entity_id, entity=entity)
        await self.uow.commit()
        self.logger.info(f"{self._entity_name} ID: {entity_id} actualizado exitosamente")
        return updated

    async def soft_delete(self, entity_id: int | UUID) -> None:
        self.logger.debug(f"Eliminando lógicamente {self._entity_name} ID: {entity_id}")
        await self.repository.soft_delete(entity_id)
        await self.uow.commit()
        self.logger.info(
            f"{self._entity_name} ID: {entity_id} eliminado exitosamente"
        )
