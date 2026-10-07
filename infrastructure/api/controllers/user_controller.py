from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from infrastructure.api.security import get_current_user
from application.services.user_service import UserService
from domain.entities.user import User
from infrastructure.api.dependencies import get_user_service
from infrastructure.api.schemas.user_schemas import (
    UserCreate,
    UserPatch,
    UserResponse,
    UserUpdate,
)
from shared.domain.pagination import PaginatedResult
from shared.infrastructure.generic_controller import PaginatedResponse

router = APIRouter(prefix="/users", tags=["Users"],  dependencies=[Depends(get_current_user)])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return await service.create_user(**payload.model_dump())


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResult[User]:
    return await service.list_page(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return await service.get_by_id(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return await service.update_user(user_id, **payload.model_dump())


@router.patch("/{user_id}", response_model=UserResponse)
async def patch_user(
    user_id: UUID,
    payload: UserPatch,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    if not payload.model_fields_set:
        return await service.get_by_id(user_id)
    # Merge logic lives in the service — the controller only translates HTTP.
    return await service.patch_user(user_id, fields=payload.model_dump(exclude_unset=True))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    await service.soft_delete(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
