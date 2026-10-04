from typing import Generic, TypeVar
from sqlalchemy.orm import Session
from shared.domain.base_repository import BaseRepository
from shared.infrastructure.exceptions import EntityNotFoundException

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

    def get_by_id(self, entity_id: int) -> M:
        orm_entity = self.db.query(self.orm_model).filter(getattr(self.orm_model, "id") == entity_id).first()
        if orm_entity is None:
            raise EntityNotFoundException(f"{self.resource_name} con ID {entity_id} no existe.")
        return self._to_domain(orm_entity)

    def get_all(self) -> list[M]:
        orm_entities = self.db.query(self.orm_model).all()
        return [self._to_domain(item) for item in orm_entities]
