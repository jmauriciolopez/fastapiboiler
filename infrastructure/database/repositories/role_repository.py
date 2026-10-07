from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.role import Role
from domain.repositories.role_repository import RoleRepositoryPort
from infrastructure.database.models.role_orm import RoleORM
from shared.infrastructure.sql_repository import SQLBaseRepository


class RoleRepository(SQLBaseRepository[Role, RoleORM], RoleRepositoryPort):
    _integrity_conflict_messages: ClassVar[dict[str, str]] = {
        "uq_roles_active_name_ci": "Ya existe un rol con ese nombre."
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Role, RoleORM, "Rol")

    def _to_domain(self, orm_entity: RoleORM) -> Role:
        return Role(
            id=orm_entity.id,
            name=orm_entity.name,
            created_on=orm_entity.created_on,
            updated_on=orm_entity.updated_on,
            deleted=orm_entity.deleted,
        )

    def _to_orm(self, entity: Role) -> RoleORM:
        return RoleORM(
            id=entity.id,
            name=entity.name,
            created_on=entity.created_on,
            updated_on=entity.updated_on,
            deleted=entity.deleted,
        )
