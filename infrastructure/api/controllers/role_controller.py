from uuid import UUID

from domain.entities.role import Role
from infrastructure.api.dependencies import get_role_service
from infrastructure.api.schemas.role_schemas import RoleCreate, RoleResponse, RoleUpdate
from shared.infrastructure.generic_controller import create_generic_router


def update_role(role_id: int | UUID, payload: RoleUpdate) -> Role:
    if not isinstance(role_id, UUID):
        raise TypeError("El ID de un rol debe ser UUID.")
    return Role(id=role_id, name=payload.name)


router = create_generic_router(
    service_provider=get_role_service,
    request_schema=RoleCreate,
    entity_factory=lambda payload: Role(name=payload.name),
    update_schema=RoleUpdate,
    update_factory=update_role,
    resource_name="Rol",
    response_schema=RoleResponse,
    entity_id_type=UUID,
    prefix="/roles",
    tags=["Roles"],
)
