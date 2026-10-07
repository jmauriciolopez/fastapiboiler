from typing import Protocol, TypeVar
from uuid import UUID

from shared.domain.pagination import PaginatedResult

T = TypeVar("T")


class RepositoryPort(Protocol[T]):
    async def save(self, entity: T) -> T: ...

    async def get_by_id(self, entity_id: int | UUID) -> T:
        """Return an active entity or raise EntityNotFoundException."""
        ...

    async def get_all(self) -> list[T]: ...

    async def get_page(self, limit: int, offset: int) -> PaginatedResult[T]: ...

    async def update(self, entity_id: int | UUID, entity: T) -> T: ...

    async def soft_delete(self, entity_id: int | UUID) -> None: ...
