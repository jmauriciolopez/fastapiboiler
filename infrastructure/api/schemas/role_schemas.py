from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    pass


class RolePatch(BaseModel):
    name: str = Field(default="", min_length=1, max_length=80)


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
