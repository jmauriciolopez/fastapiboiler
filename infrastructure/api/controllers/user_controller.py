from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

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

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return service.create_user(**payload.model_dump())


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResult[User]:
    return service.list_page(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return service.get_by_id(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    return service.update_user(user_id, **payload.model_dump())


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: UUID,
    payload: UserPatch,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    current = service.get_by_id(user_id)
    if not payload.model_fields_set:
        return current
    values = payload.model_dump(exclude_unset=True)
    return service.update_user(
        user_id,
        username=values.get("username", current.username),
        email=values.get("email", current.email),
        phone=values.get("phone", current.phone),
        status=values.get("status", current.status),
        role_ids=values.get("role_ids", [role.id for role in current.roles]),
        password=values.get("password"),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    service.soft_delete(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
