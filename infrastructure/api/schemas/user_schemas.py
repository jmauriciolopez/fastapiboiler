from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from domain.entities.user import UserStatus
from infrastructure.api.schemas.role_schemas import RoleResponse


class UserRoleIdsMixin(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list)

    @field_validator("role_ids")
    @classmethod
    def role_ids_must_be_unique(cls, role_ids: list[UUID]) -> list[UUID]:
        if len(role_ids) != len(set(role_ids)):
            raise ValueError("No se permiten roles duplicados.")
        return role_ids


class UserCreate(UserRoleIdsMixin):
    username: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=8, max_length=128, repr=False)


class UserUpdate(UserRoleIdsMixin):
    username: str = Field(min_length=1, max_length=150)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=32)
    status: UserStatus
    password: str | None = Field(default=None, min_length=8, max_length=128, repr=False)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    phone: str
    status: UserStatus
    roles: list[RoleResponse]
