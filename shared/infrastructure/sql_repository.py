from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.application.pagination import PaginatedResult
from shared.domain.base_repository import BaseRepository
from shared.domain.exceptions import EntityNotFoundException

M = TypeVar("M")
O = TypeVar("O")

class SQLBaseRepository(BaseRepository[M], Generic[M, O]):
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
        entity_data = {
            column.name: getattr(entity, column.name)
            for column in self.orm_model.__table__.columns
            if hasattr(entity, column.name)
        }
        orm_entity = self.orm_model(**entity_data)
        self.db.add(orm_entity)
        self.db.commit()
        self.db.refresh(orm_entity)
        return self._to_domain(orm_entity)

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
            orm_entity.updated_on = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(orm_entity)
        return self._to_domain(orm_entity)

    def soft_delete(self, entity_id: int | UUID) -> None:
        orm_entity = self._get_active_orm_entity(entity_id)
        if not hasattr(orm_entity, "deleted"):
            raise TypeError(f"{self.orm_model.__name__} debe implementar el campo 'deleted'.")
        orm_entity.deleted = True
        if hasattr(orm_entity, "updated_on"):
            orm_entity.updated_on = datetime.now(UTC)
        self.db.commit()

    def _active_query(self):
        query = self.db.query(self.orm_model)
        if hasattr(self.orm_model, "deleted"):
            query = query.filter(self.orm_model.deleted.is_(False))
        return query

    def _get_active_orm_entity(self, entity_id: int | UUID) -> O:
        orm_entity = self._active_query().filter(self.orm_model.id == entity_id).first()
        if orm_entity is None:
            raise EntityNotFoundException(f"{self.resource_name} con ID {entity_id} no existe.")
        return orm_entity
