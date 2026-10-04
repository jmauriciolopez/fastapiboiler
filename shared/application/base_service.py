from typing import Generic, TypeVar
from uuid import UUID

from shared.application.pagination import PaginatedResult
from shared.domain.base_repository import BaseRepository

M = TypeVar("M")

class BaseService(Generic[M]):
    def __init__(self, repository: BaseRepository[M]) -> None:
        self.repository = repository

    def create(self, entity: M) -> M:
        return self.repository.save(entity)

    def get_by_id(self, entity_id: int | UUID) -> M | None:
        return self.repository.get_by_id(entity_id)

    def list_all(self) -> list[M]:
        return self.repository.get_all()

    def list_page(self, limit: int, offset: int) -> PaginatedResult[M]:
        return self.repository.get_page(limit=limit, offset=offset)

    def update(self, entity_id: int | UUID, entity: M) -> M:
        return self.repository.update(entity_id=entity_id, entity=entity)

    def soft_delete(self, entity_id: int | UUID) -> None:
        self.repository.soft_delete(entity_id)
