from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    rol: str = Field(min_length=1, max_length=80)


class RoleUpdate(BaseModel):
    rol: str = Field(min_length=1, max_length=80)


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rol: str
