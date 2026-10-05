from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Query, Session, selectinload

from domain.entities.role import Role
from domain.entities.user import User
from domain.repositories.user_repository import UserRepositoryPort
from infrastructure.database.models.role_orm import RoleORM
from infrastructure.database.models.user_orm import UserORM
from shared.domain.exceptions import EntityNotFoundException
from shared.infrastructure.sql_repository import SQLBaseRepository


class UserRepository(SQLBaseRepository[User, UserORM], UserRepositoryPort):
    _integrity_conflict_messages: ClassVar[dict[str, str]] = {
        "uq_users_active_email_ci": "Ya existe un usuario con ese correo.",
        "uq_users_active_username_ci": "Ya existe un usuario con ese nombre de usuario.",
    }

    def __init__(self, db: Session) -> None:
        super().__init__(db, User, UserORM, "Usuario")

    def _active_query(self) -> Query[UserORM]:
        return (
            super()
            ._active_query()
            .options(selectinload(UserORM.roles))
        )

    def _to_domain(self, orm_entity: UserORM) -> User:
        roles = [
            Role(
                id=role.id,
                name=role.name,
                created_on=role.created_on,
                updated_on=role.updated_on,
                deleted=role.deleted,
            )
            for role in orm_entity.roles
            if not role.deleted
        ]
        return User(
            id=orm_entity.id,
            username=orm_entity.username,
            email=orm_entity.email,
            phone=orm_entity.phone,
            hashed_password=orm_entity.hashed_password,
            status=orm_entity.status,
            roles=roles,
            created_on=orm_entity.created_on,
            updated_on=orm_entity.updated_on,
            deleted=orm_entity.deleted,
        )

    def get_by_username(self, username: str) -> User | None:
        """Busca un usuario activo por nombre de usuario, sin distinguir mayúsculas.

        La comparación es insensible a mayúsculas para ser coherente con el
        índice único parcial ``uq_users_active_username_ci``.
        """
        orm_entity = (
            self._active_query()
            .filter(func.lower(UserORM.username) == username.lower())
            .first()
        )
        return None if orm_entity is None else self._to_domain(orm_entity)

    def get_active_roles(self, role_ids: list[UUID]) -> list[Role]:
        if not role_ids:
            return []
        orm_roles = (
            self.db.query(RoleORM)
            .filter(RoleORM.id.in_(role_ids), RoleORM.deleted.is_(False))
            .all()
        )
        if len(orm_roles) != len(role_ids):
            found_ids = {role.id for role in orm_roles}
            missing_ids = [role_id for role_id in role_ids if role_id not in found_ids]
            raise EntityNotFoundException(f"No existen roles activos con IDs: {missing_ids}.")
        return [
            Role(
                id=role.id,
                name=role.name,
                created_on=role.created_on,
                updated_on=role.updated_on,
                deleted=role.deleted,
            )
            for role in orm_roles
        ]

    def _get_role_orms(self, roles: list[Role]) -> list[RoleORM]:
        role_ids = [role.id for role in roles]
        if not role_ids:
            return []
        orm_roles = (
            self.db.query(RoleORM)
            .filter(RoleORM.id.in_(role_ids), RoleORM.deleted.is_(False))
            .all()
        )
        if len(orm_roles) != len(role_ids):
            raise EntityNotFoundException("Uno o más roles no existen o están eliminados.")
        return orm_roles

    def _to_orm(self, entity: User) -> UserORM:
        orm_entity = UserORM(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            phone=entity.phone,
            hashed_password=entity.hashed_password,
            status=entity.status,
            created_on=entity.created_on,
            updated_on=entity.updated_on,
            deleted=entity.deleted,
            roles=self._get_role_orms(entity.roles),
        )
        return orm_entity

    def update(self, entity_id: int | UUID, entity: User) -> User:
        orm_entity = self._get_active_orm_entity(entity_id)
        role_orms = self._get_role_orms(entity.roles)

        orm_entity.username = entity.username
        orm_entity.email = entity.email
        orm_entity.phone = entity.phone
        orm_entity.hashed_password = entity.hashed_password
        orm_entity.status = entity.status
        orm_entity.roles = role_orms
        orm_entity.updated_on = datetime.now(UTC)
        self._commit()
        self.db.refresh(orm_entity)
        return self._to_domain(orm_entity)
