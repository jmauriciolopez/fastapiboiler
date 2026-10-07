"""Generic async CRUD router factory.

Creates standard Create / Read / Update / Delete / List endpoints for any
entity that has a ``BaseService``.  Routes are registered with ``async def``
handlers so FastAPI's ASGI event loop is never blocked.
"""

from collections.abc import Callable,Sequence
from enum import Enum
from inspect import signature
from typing import Any, Generic, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, create_model

from shared.application.base_service import BaseService
from shared.domain.pagination import PaginatedResult

M = TypeVar("M")
RequestSchema = TypeVar("RequestSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)
PatchSchema = TypeVar("PatchSchema", bound=BaseModel)
ResponseItem = TypeVar("ResponseItem")


class PaginatedResponse(BaseModel, Generic[ResponseItem]):
    items: list[ResponseItem]
    total: int
    limit: int
    offset: int


def _create_paginated_response_schema(
    response_schema: type[BaseModel],
) -> type[BaseModel]:
    item_list_schema = list[response_schema]  # type: ignore[valid-type]
    return create_model(
        f"Paginated{response_schema.__name__}",
        items=(item_list_schema, ...),
        total=(int, ...),
        limit=(int, ...),
        offset=(int, ...),
    )


def _with_parameter_types(
    endpoint: Callable[..., Any],
    parameter_types: dict[str, Any],
) -> None:
    """Patch ``__signature__`` so FastAPI introspects the concrete types."""
    endpoint_signature = signature(endpoint)
    parameters = [
        parameter.replace(
            annotation=parameter_types.get(parameter.name, parameter.annotation)
        )
        for parameter in endpoint_signature.parameters.values()
    ]
    endpoint.__signature__ = endpoint_signature.replace(  # type: ignore[attr-defined]
        parameters=parameters
    )


def create_generic_router(
    service_provider: Callable[..., BaseService[M]],
    request_schema: type[RequestSchema],
    entity_factory: Callable[[RequestSchema], M],
    update_schema: type[UpdateSchema],
    update_factory: Callable[[int | UUID, UpdateSchema], M],
    resource_name: str,
    response_schema: type[BaseModel],
    entity_id_type: type[int] | type[UUID] = int,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    default_page_size: int = 20,
    max_page_size: int = 100,
    patch_schema: type[PatchSchema] | None = None,
    patch_factory: Callable[[int | UUID, M, PatchSchema], M] | None = None,
     dependencies: Sequence[Any] | None = None,
) -> APIRouter:
    if (patch_schema is None) != (patch_factory is None):
        raise ValueError("patch_schema y patch_factory deben configurarse juntos.")

    router = APIRouter(prefix=prefix, tags=tags, dependencies=list(dependencies or []))
    paginated_response_schema = _create_paginated_response_schema(response_schema)

    # ------------------------------------------------------------------ create
    async def create(
        payload: RequestSchema,
        service: BaseService[M] = Depends(service_provider),  # noqa: B008
    ) -> M:
        return await service.create(entity_factory(payload))

    _with_parameter_types(create, {"payload": request_schema})
    router.add_api_route(
        "/",
        create,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        summary=f"Crear un {resource_name}",
        response_model=response_schema,
    )

    # --------------------------------------------------------------- get by id
    async def get_by_id(
        entity_id: int | UUID,
        service: BaseService[M] = Depends(service_provider),  # noqa: B008
    ) -> M:
        return await service.get_by_id(entity_id)

    _with_parameter_types(get_by_id, {"entity_id": entity_id_type})
    router.add_api_route(
        "/{entity_id}",
        get_by_id,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary=f"Obtener un {resource_name} por ID",
        response_model=response_schema,
    )

    # ------------------------------------------------------------------ update
    async def update(
        entity_id: int | UUID,
        payload: UpdateSchema,
        service: BaseService[M] = Depends(service_provider),  # noqa: B008
    ) -> M:
        return await service.update(entity_id, update_factory(entity_id, payload))

    _with_parameter_types(update, {"entity_id": entity_id_type, "payload": update_schema})
    router.add_api_route(
        "/{entity_id}",
        update,
        methods=["PUT"],
        status_code=status.HTTP_200_OK,
        summary=f"Actualizar un {resource_name}",
        response_model=response_schema,
    )

    # ------------------------------------------------------------------- patch
    if patch_schema is not None and patch_factory is not None:

        async def patch(
            entity_id: int | UUID,
            payload: PatchSchema,
            service: BaseService[M] = Depends(service_provider),  # noqa: B008
        ) -> M:
            current = await service.get_by_id(entity_id)
            if not payload.model_fields_set:
                return current
            return await service.update(
                entity_id,
                patch_factory(entity_id, current, payload),
            )

        _with_parameter_types(
            patch,
            {"entity_id": entity_id_type, "payload": patch_schema},
        )
        router.add_api_route(
            "/{entity_id}",
            patch,
            methods=["PATCH"],
            status_code=status.HTTP_200_OK,
            summary=f"Actualizar parcialmente un {resource_name}",
            response_model=response_schema,
        )

    # --------------------------------------------------------------- delete
    async def soft_delete(
        entity_id: int | UUID,
        service: BaseService[M] = Depends(service_provider),  # noqa: B008
    ) -> Response:
        await service.soft_delete(entity_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    _with_parameter_types(soft_delete, {"entity_id": entity_id_type})
    router.add_api_route(
        "/{entity_id}",
        soft_delete,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Eliminar lógicamente un {resource_name}",
        response_class=Response,
    )

    # ----------------------------------------------------------------- list
    async def list_all(
        limit: int = Query(default_page_size, ge=1, le=max_page_size),
        offset: int = Query(0, ge=0),
        service: BaseService[M] = Depends(service_provider),  # noqa: B008
    ) -> PaginatedResult[M]:
        return await service.list_page(limit=limit, offset=offset)

    router.add_api_route(
        "/",
        list_all,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary=f"Listar {resource_name}s con paginación",
        response_model=paginated_response_schema,
    )

    return router
