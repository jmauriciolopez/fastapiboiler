from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.entities.user import UserStatus
from infrastructure.database.models.role_orm import RoleORM, user_roles
from shared.infrastructure.persistence.database import Base


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "uq_users_active_email_ci",
            text("lower(email)"),
            unique=True,
            postgresql_where=text("deleted = false"),
            sqlite_where=text("deleted = 0"),
        ),
        Index(
            "uq_users_active_username_ci",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("deleted = false"),
            sqlite_where=text("deleted = 0"),
        ),
    )

    # Los nombres de atributo se alinean con la entidad de dominio; las columnas
    # físicas conservan su nombre original para no requerir migración.
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    username: Mapped[str] = mapped_column("name", String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    hashed_password: Mapped[str] = mapped_column("password_hash", String(255), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            native_enum=False,
            values_callable=lambda enum_type: [member.value for member in enum_type],
            length=16,
        ),
        nullable=False,
        default=UserStatus.PENDING,
    )
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    roles: Mapped[list[RoleORM]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )
