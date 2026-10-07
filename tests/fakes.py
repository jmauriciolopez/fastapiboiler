"""Shared test doubles used by both unit and integration suites.

A single generic in-memory repository avoids duplicating a fake per entity type.
All repository methods are async to match the updated ``RepositoryPort`` contract.
"""

from typing import Any, ClassVar, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from shared.application.ports.logger import LoggerPort
from shared.application.unit_of_work import UnitOfWork
from shared.domain.exceptions import EntityNotFoundException
from shared.domain.pagination import PaginatedResult
from shared.domain.repository_port import RepositoryPort

T = TypeVar("T")


class FakeLogger(LoggerPort):
    """No-op logger for tests."""

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass


class FakeUnitOfWork:
    """No-op UoW — commits and rollbacks are no-ops in tests."""

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def flush(self) -> None:
        pass


class InMemoryRepository(RepositoryPort[T]):
    """In-memory implementation of ``RepositoryPort``.

    Respects the port contract:
    - ``get_by_id`` and ``update`` raise ``EntityNotFoundException`` when missing
      or soft-deleted.
    - ``soft_delete`` only marks the entity; it does not remove it.
    """

    def __init__(self) -> None:
        self.entities: dict[int | UUID, T] = {}
        self.deleted: set[int | UUID] = set()
        self._last_id = 0

    def _next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def _require_active(self, entity_id: int | UUID) -> None:
        if entity_id in self.deleted or entity_id not in self.entities:
            raise EntityNotFoundException(f"Recurso con ID {entity_id} no existe.")

    async def save(self, entity: T) -> T:
        self.entities[self._next_id()] = entity
        return entity

    async def get_by_id(self, entity_id: int | UUID) -> T:
        self._require_active(entity_id)
        return self.entities[entity_id]

    async def get_all(self) -> list[T]:
        return [
            entity
            for entity_id, entity in self.entities.items()
            if entity_id not in self.deleted
        ]

    async def get_page(self, limit: int, offset: int) -> PaginatedResult[T]:
        items = await self.get_all()
        return PaginatedResult(items[offset: offset + limit], len(items), limit, offset)

    async def update(self, entity_id: int | UUID, entity: T) -> T:
        self._require_active(entity_id)
        self.entities[entity_id] = entity
        return entity

    async def soft_delete(self, entity_id: int | UUID) -> None:
        self.deleted.add(entity_id)


class PayloadSchema(BaseModel):
    """Minimal response schema for generic router tests."""

    name: str


class PayloadPatchSchema(BaseModel):
    """Partial schema for PATCH route tests."""

    name: str = Field(default="")


class ValidatedPayloadSchema(BaseModel):
    """Counts validations to catch double-validation of the payload."""

    name: str
    validation_count: ClassVar[int] = 0

    @field_validator("name")
    @classmethod
    def count_validation(cls, name: str) -> str:
        cls.validation_count += 1
        return name
