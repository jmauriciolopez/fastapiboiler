"""Dobles de prueba compartidos por las suites unitaria y de integración.

Un único repositorio en memoria, genérico sobre el tipo de entidad, evita
duplicar un fake por cada tipo que se quiera probar.
"""

from typing import Any, ClassVar, TypeVar
from uuid import UUID

from pydantic import BaseModel, field_validator

from application.ports.logger import LoggerPort
from shared.domain.exceptions import EntityNotFoundException
from shared.domain.pagination import PaginatedResult
from shared.domain.repository_port import RepositoryPort

T = TypeVar("T")


class FakeLogger(LoggerPort):
    """Logger sin efectos secundarios para pruebas."""

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


class InMemoryRepository(RepositoryPort[T]):
    """Implementación en memoria del contrato ``RepositoryPort``.

    Respeta las reglas del puerto: ``get_by_id`` y ``update`` lanzan
    ``EntityNotFoundException`` cuando la entidad no existe o fue eliminada,
    y ``soft_delete`` solo marca la entidad como eliminada.
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

    def save(self, entity: T) -> T:
        self.entities[self._next_id()] = entity
        return entity

    def get_by_id(self, entity_id: int | UUID) -> T:
        self._require_active(entity_id)
        return self.entities[entity_id]

    def get_all(self) -> list[T]:
        return [
            entity
            for entity_id, entity in self.entities.items()
            if entity_id not in self.deleted
        ]

    def get_page(self, limit: int, offset: int) -> PaginatedResult[T]:
        items = self.get_all()
        return PaginatedResult(items[offset : offset + limit], len(items), limit, offset)

    def update(self, entity_id: int | UUID, entity: T) -> T:
        self._require_active(entity_id)
        self.entities[entity_id] = entity
        return entity

    def soft_delete(self, entity_id: int | UUID) -> None:
        self.deleted.add(entity_id)


class PayloadSchema(BaseModel):
    """Esquema de respuesta mínimo para las pruebas del router genérico."""

    name: str


class ValidatedPayloadSchema(BaseModel):
    """Cuenta las validaciones para detectar una doble validación del payload."""

    name: str
    validation_count: ClassVar[int] = 0

    @field_validator("name")
    @classmethod
    def count_validation(cls, name: str) -> str:
        cls.validation_count += 1
        return name
