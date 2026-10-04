from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from domain.entities.role import Role
from infrastructure.api.schemas.role_schemas import RoleCreate, RoleResponse, RoleUpdate
from infrastructure.database.models.role_orm import RoleORM
from shared.application.base_service import BaseService
from shared.infrastructure.database import get_db
from shared.infrastructure.generic_controller import create_generic_router
from shared.infrastructure.sql_repository import SQLBaseRepository


def get_role_service(db: Annotated[Session, Depends(get_db)]) -> BaseService[Role]:
    repository = SQLBaseRepository(
        db=db,
        domain_model=Role,
        orm_model=RoleORM,
        resource_name="Rol",
    )
    return BaseService(repository)


router = create_generic_router(
    service_provider=get_role_service,
    request_schema=RoleCreate,
    entity_factory=lambda payload: Role(rol=payload.rol),
    update_schema=RoleUpdate,
    update_factory=lambda role_id, payload: Role(id=role_id, rol=payload.rol),
    resource_name="Rol",
    response_schema=RoleResponse,
    entity_id_type=UUID,
    prefix="/roles",
    tags=["Roles"],
)
