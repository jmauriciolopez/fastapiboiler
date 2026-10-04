from typing import Any, Callable, TypeVar
from fastapi import APIRouter, status
from pydantic import BaseModel
from shared.application.base_service import BaseService

M = TypeVar("M")
RequestSchema = TypeVar("RequestSchema", bound=BaseModel)

def create_generic_router(
    service_instance: BaseService[M],
    request_schema: type[RequestSchema],
    entity_factory: Callable[[RequestSchema], M],
    resource_name: str,
) -> APIRouter:
    router = APIRouter()

    def create(payload: BaseModel) -> Any:
        validated_payload = request_schema.model_validate(payload.model_dump())
        return service_instance.create(entity_factory(validated_payload))

    create.__annotations__["payload"] = request_schema
    router.add_api_route(
        "/",
        create,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        summary=f"Crear un {resource_name}",
    )

    @router.get("/{entity_id}", status_code=status.HTTP_200_OK, summary=f"Obtener un {resource_name} por ID")
    def get_by_id(entity_id: int) -> Any:
        return service_instance.get_by_id(entity_id)

    @router.get("/", status_code=status.HTTP_200_OK, summary=f"Listar todos los {resource_name}s")
    def list_all() -> Any:
        return service_instance.list_all()

    return router
