"""Async generic SQLAlchemy repository.

Repositories no longer own the transaction: they add/merge objects to the
session and flush, but never call ``session.commit()``.  The Unit of Work
(owned by the application service) decides when to commit.

Subclasses MUST override ``_to_domain`` and ``_to_orm`` — the base
implementations are intentionally abstract so that column-aliasing bugs
(e.g. ORM column named "name" mapped to domain attribute "username") are
caught at class-definition time rather than silently at runtime.
"""

from abc import abstractmethod
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import ClassVar, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from shared.domain.exceptions import DomainConflictException, EntityNotFoundException
from shared.domain.pagination import PaginatedResult
from shared.domain.repository_port import RepositoryPort
from shared.infrastructure.integrity_errors import violates_unique_constraint

M = TypeVar("M")
O = TypeVar("O", bound=DeclarativeBase)


class SQLBaseRepository(RepositoryPort[M], Generic[M, O]):
    _integrity_conflict_messages: ClassVar[Mapping[str, str]] = {}

    def __init__(
        self,
        session: AsyncSession,
        domain_model: type[M],
        orm_model: type[O],
        resource_name: str = "Recurso",
    ) -> None:
        self.session = session
        self.domain_model = domain_model
        self.orm_model = orm_model
        self.resource_name = resource_name

    # ------------------------------------------------------------------
    # Subclasses must implement these two methods to avoid silent mapping
    # bugs caused by ORM column aliases diverging from domain attributes.
    # ------------------------------------------------------------------

    @abstractmethod
    def _to_domain(self, orm_entity: O) -> M:
        """Convert an ORM row to a pure domain entity."""

    @abstractmethod
    def _to_orm(self, entity: M) -> O:
        """Convert a domain entity to an ORM model instance."""

    # ------------------------------------------------------------------
    # CRUD — no commit calls; the Unit of Work owns the transaction.
    # ------------------------------------------------------------------

    async def save(self, entity: M) -> M:
        orm_entity = self._to_orm(entity)
        self.session.add(orm_entity)
        await self._flush()
        await self.session.refresh(orm_entity)
        return self._to_domain(orm_entity)

    async def get_by_id(self, entity_id: int | UUID) -> M:
        return self._to_domain(await self._get_active_orm_entity(entity_id))

    async def get_all(self) -> list[M]:
        stmt = self._active_select()
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def get_page(self, limit: int, offset: int) -> PaginatedResult[M]:
        base_stmt = self._active_select()

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = (await self.session.execute(count_stmt)).scalar_one()

        page_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(page_stmt)
        items = [self._to_domain(row) for row in result.scalars().all()]

        return PaginatedResult(items=items, total=total, limit=limit, offset=offset)

    async def update(self, entity_id: int | UUID, entity: M) -> M:
        orm_entity = await self._get_active_orm_entity(entity_id)
        columns = {column.name for column in self.orm_model.__table__.columns}
        excluded_fields = {"id", "deleted", "created_on", "updated_on"}
        for field_name in columns - excluded_fields:
            if hasattr(entity, field_name):
                setattr(orm_entity, field_name, getattr(entity, field_name))
        if "updated_on" in columns:
            self._set_orm_attribute(orm_entity, "updated_on", datetime.now(UTC))
        await self._flush()
        await self.session.refresh(orm_entity)
        return self._to_domain(orm_entity)

    async def soft_delete(self, entity_id: int | UUID) -> None:
        orm_entity = await self._get_active_orm_entity(entity_id)
        if not hasattr(orm_entity, "deleted"):
            raise TypeError(
                f"{self.orm_model.__name__} debe implementar el campo 'deleted'."
            )
        orm_entity.deleted = True  # type: ignore[attr-defined]
        if hasattr(orm_entity, "updated_on"):
            orm_entity.updated_on = datetime.now(UTC)  # type: ignore[attr-defined]
        await self._flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _flush(self) -> None:
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            self._handle_integrity_error(exc)
            raise

    def _handle_integrity_error(self, exc: IntegrityError) -> None:
        for constraint_name, message in self._integrity_conflict_messages.items():
            if violates_unique_constraint(exc, constraint_name):
                raise DomainConflictException(message) from exc

    @staticmethod
    def _set_orm_attribute(entity: O, field_name: str, value: object) -> None:
        setattr(entity, field_name, value)

    def _active_select(self):  # type: ignore[return]
        """Return a SELECT statement filtered to non-deleted rows."""
        stmt = select(self.orm_model)
        deleted_column = getattr(self.orm_model, "deleted", None)
        if deleted_column is not None:
            stmt = stmt.where(deleted_column.is_(False))
        return stmt

    async def _get_active_orm_entity(self, entity_id: int | UUID) -> O:
        id_column = getattr(self.orm_model, "id")
        stmt = self._active_select().where(id_column == entity_id)
        result = await self.session.execute(stmt)
        orm_entity = result.scalars().first()
        if orm_entity is None:
            raise EntityNotFoundException(
                f"{self.resource_name} con ID {entity_id} no existe."
            )
        return orm_entity
