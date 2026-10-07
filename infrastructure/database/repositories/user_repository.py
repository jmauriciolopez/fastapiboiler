from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities.role import Role
from domain.entities.user import User, UserStatus
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

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User, UserORM, "Usuario")

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

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
            # Convert VARCHAR → domain enum at the anti-corruption boundary
            status=UserStatus(orm_entity.status),
            roles=roles,
            created_on=orm_entity.created_on,
            updated_on=orm_entity.updated_on,
            deleted=orm_entity.deleted,
        )

    def _to_orm(self, entity: User) -> UserORM:
        # Roles are resolved separately via _get_role_orms before calling save();
        # on a plain save() the domain entity carries populated Role objects whose
        # IDs we use to load the ORM counterparts.
        return UserORM(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            phone=entity.phone,
            hashed_password=entity.hashed_password,
            status=entity.status.value,  # enum → string, no domain import in ORM
            created_on=entity.created_on,
            updated_on=entity.updated_on,
            deleted=entity.deleted,
            # Roles are attached by save() / update() after async role resolution
        )

    # ------------------------------------------------------------------
    # Queries that load the roles relationship
    # ------------------------------------------------------------------

    def _active_select(self):  # type: ignore[override]
        return (
            super()
            ._active_select()
            .options(selectinload(UserORM.roles))
        )

    # ------------------------------------------------------------------
    # Override save() to attach resolved role ORM objects
    # ------------------------------------------------------------------

    async def save(self, entity: User) -> User:
        role_orms = await self._get_role_orms(entity.roles)
        orm_entity = self._to_orm(entity)
        orm_entity.roles = role_orms
        self.session.add(orm_entity)
        await self._flush()
        await self.session.refresh(orm_entity)
        return self._to_domain(orm_entity)

    # ------------------------------------------------------------------
    # Override update() to sync the roles relationship
    # ------------------------------------------------------------------

    async def update(self, entity_id: int | UUID, entity: User) -> User:
        orm_entity = await self._get_active_orm_entity(entity_id)
        role_orms = await self._get_role_orms(entity.roles)

        orm_entity.username = entity.username
        orm_entity.email = entity.email
        orm_entity.phone = entity.phone
        orm_entity.hashed_password = entity.hashed_password
        orm_entity.status = entity.status.value
        orm_entity.roles = role_orms
        orm_entity.updated_on = datetime.now(UTC)

        await self._flush()
        await self.session.refresh(orm_entity)
        return self._to_domain(orm_entity)

    # ------------------------------------------------------------------
    # Domain-specific queries
    # ------------------------------------------------------------------

    async def get_by_username(self, username: str) -> User | None:
        """Case-insensitive lookup — consistent with the partial unique index."""
        stmt = (
            self._active_select()
            .where(func.lower(UserORM.username) == username.lower())
        )
        result = await self.session.execute(stmt)
        orm_entity = result.scalars().first()
        return None if orm_entity is None else self._to_domain(orm_entity)

    async def get_active_roles(self, role_ids: list[UUID]) -> list[Role]:
        if not role_ids:
            return []
        stmt = select(RoleORM).where(
            RoleORM.id.in_(role_ids),
            RoleORM.deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        orm_roles = result.scalars().all()

        if len(orm_roles) != len(role_ids):
            found_ids = {role.id for role in orm_roles}
            missing_ids = [rid for rid in role_ids if rid not in found_ids]
            raise EntityNotFoundException(
                f"No existen roles activos con IDs: {missing_ids}."
            )

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

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    async def _get_role_orms(self, roles: list[Role]) -> list[RoleORM]:
        role_ids = [role.id for role in roles]
        if not role_ids:
            return []
        stmt = select(RoleORM).where(
            RoleORM.id.in_(role_ids),
            RoleORM.deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        orm_roles = result.scalars().all()
        if len(orm_roles) != len(role_ids):
            raise EntityNotFoundException(
                "Uno o más roles no existen o están eliminados."
            )
        return list(orm_roles)
