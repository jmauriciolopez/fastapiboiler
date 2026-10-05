from collections.abc import Mapping
from datetime import UTC, datetime
from typing import ClassVar, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Query, Session

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
        db: Session,
        domain_model: type[M],
        orm_model: type[O],
        resource_name: str = "Recurso",
    ) -> None:
        self.db = db
        self.domain_model = domain_model
        self.orm_model = orm_model
        self.resource_name = resource_name

    def _to_domain(self, orm_entity: O) -> M:
        return self.domain_model(**{c.name: getattr(orm_entity, c.name) for c in orm_entity.__table__.columns})

    def save(self, entity: M) -> M:
        orm_entity = self._to_orm(entity)
        self.db.add(orm_entity)
        self._commit()
        self.db.refresh(orm_entity)
        return self._to_domain(orm_entity)

    def _to_orm(self, entity: M) -> O:
        entity_data = {
            column.name: getattr(entity, column.name)
            for column in self.orm_model.__table__.columns
            if hasattr(entity, column.name)
        }
        return self.orm_model(**entity_data)

    def get_by_id(self, entity_id: int | UUID) -> M:
        return self._to_domain(self._get_active_orm_entity(entity_id))

    def get_all(self) -> list[M]:
        orm_entities = self._active_query().all()
        return [self._to_domain(item) for item in orm_entities]

    def get_page(self, limit: int, offset: int) -> PaginatedResult[M]:
        query = self._active_query()
        total = query.with_entities(func.count()).scalar() or 0
        orm_entities = query.offset(offset).limit(limit).all()
        return PaginatedResult(
            items=[self._to_domain(item) for item in orm_entities],
            total=total,
            limit=limit,
            offset=offset,
        )

    def update(self, entity_id: int | UUID, entity: M) -> M:
        orm_entity = self._get_active_orm_entity(entity_id)
        columns = {column.name for column in self.orm_model.__table__.columns}
        excluded_fields = {"id", "deleted", "created_on", "updated_on"}
        for field_name in columns - excluded_fields:
            if hasattr(entity, field_name):
                setattr(orm_entity, field_name, getattr(entity, field_name))
        if "updated_on" in columns:
            self._set_orm_attribute(orm_entity, "updated_on", datetime.now(UTC))
        self._commit()
        self.db.refresh(orm_entity)
        return self._to_domain(orm_entity)

    def soft_delete(self, entity_id: int | UUID) -> None:
        orm_entity = self._get_active_orm_entity(entity_id)
        if not hasattr(orm_entity, "deleted"):
            raise TypeError(f"{self.orm_model.__name__} debe implementar el campo 'deleted'.")
        orm_entity.deleted = True
        if hasattr(orm_entity, "updated_on"):
            orm_entity.updated_on = datetime.now(UTC)
        self._commit()

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            self._handle_integrity_error(exc)
            raise
        except Exception:
            self.db.rollback()
            raise

    def _handle_integrity_error(self, exc: IntegrityError) -> None:
        for constraint_name, message in self._integrity_conflict_messages.items():
            if violates_unique_constraint(exc, constraint_name):
                raise DomainConflictException(message) from exc

    @staticmethod
    def _set_orm_attribute(entity: O, field_name: str, value: object) -> None:
        setattr(entity, field_name, value)

    def _active_query(self) -> Query[O]:
        query = self.db.query(self.orm_model)
        deleted_column = getattr(self.orm_model, "deleted", None)
        if deleted_column is not None:
            query = query.filter(deleted_column.is_(False))
        return query

    def _get_active_orm_entity(self, entity_id: int | UUID) -> O:
        id_field_name = "id"
        id_column = getattr(self.orm_model, id_field_name)
        orm_entity = self._active_query().filter(id_column == entity_id).first()
        if orm_entity is None:
            raise EntityNotFoundException(f"{self.resource_name} con ID {entity_id} no existe.")
        return orm_entity
