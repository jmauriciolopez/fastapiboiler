from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from shared.application.pagination import PaginatedResult

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> T:
        ...

    @abstractmethod
    def get_by_id(self, entity_id: int | UUID) -> T | None:
        ...

    @abstractmethod
    def get_all(self) -> list[T]:
        ...

    @abstractmethod
    def get_page(self, limit: int, offset: int) -> PaginatedResult[T]:
        ...

    @abstractmethod
    def update(self, entity_id: int | UUID, entity: T) -> T:
        ...

    @abstractmethod
    def soft_delete(self, entity_id: int | UUID) -> None:
        ...
