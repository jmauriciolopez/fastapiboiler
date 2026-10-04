from typing import Generic, TypeVar

from shared.domain.base_repository import BaseRepository

M = TypeVar("M")

class BaseService(Generic[M]):
    def __init__(self, repository: BaseRepository[M]) -> None:
        self.repository = repository

    def create(self, entity: M) -> M:
        return self.repository.save(entity)

    def get_by_id(self, entity_id: int) -> M | None:
        return self.repository.get_by_id(entity_id)

    def list_all(self) -> list[M]:
        return self.repository.get_all()
