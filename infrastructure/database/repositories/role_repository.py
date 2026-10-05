from typing import ClassVar

from sqlalchemy.orm import Session

from domain.entities.role import Role
from domain.repositories.role_repository import RoleRepositoryPort
from infrastructure.database.models.role_orm import RoleORM
from shared.infrastructure.sql_repository import SQLBaseRepository


class RoleRepository(SQLBaseRepository[Role, RoleORM], RoleRepositoryPort):
    _integrity_conflict_messages: ClassVar[dict[str, str]] = {
        "uq_roles_active_name_ci": "Ya existe un rol con ese nombre."
    }

    def __init__(self, db: Session) -> None:
        super().__init__(db, Role, RoleORM, "Rol")
