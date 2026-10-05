from typing import Generic, TypeVar
from uuid import UUID

from shared.domain.pagination import PaginatedResult
from shared.domain.repository_port import RepositoryPort
from application.ports.logger import LoggerPort

M = TypeVar("M")

class BaseService(Generic[M]):
    def __init__(self, repository: RepositoryPort[M], logger: LoggerPort) -> None:
        self.repository = repository
        self.logger = logger
        self._entity_name = self.__class__.__name__.replace("Service", "")

    def create(self, entity: M) -> M:
        self.logger.debug(f"Creando nuevo {self._entity_name}")
        saved = self.repository.save(entity)
        self.logger.info(f"{self._entity_name} creado exitosamente")
        return saved

    def get_by_id(self, entity_id: int | UUID) -> M:
        self.logger.debug(f"Buscando {self._entity_name} por ID: {entity_id}")
        return self.repository.get_by_id(entity_id)

    def list_all(self) -> list[M]:
        self.logger.debug(f"Listando todos los {self._entity_name}")
        return self.repository.get_all()

    def list_page(self, limit: int, offset: int) -> PaginatedResult[M]:
        self.logger.debug(f"Listando {self._entity_name} (página limit={limit}, offset={offset})")
        return self.repository.get_page(limit=limit, offset=offset)

    def update(self, entity_id: int | UUID, entity: M) -> M:
        self.logger.debug(f"Actualizando {self._entity_name} ID: {entity_id}")
        updated = self.repository.update(entity_id=entity_id, entity=entity)
        self.logger.info(f"{self._entity_name} ID: {entity_id} actualizado exitosamente")
        return updated

    def soft_delete(self, entity_id: int | UUID) -> None:
        self.logger.debug(f"Eliminando lógicamente {self._entity_name} ID: {entity_id}")
        self.repository.soft_delete(entity_id)
        self.logger.info(f"{self._entity_name} ID: {entity_id} eliminado exitosamente")
