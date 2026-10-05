from typing import Annotated

from fastapi import APIRouter, Depends

from application.services.auth_service import AuthService
from domain.entities.user import User
from infrastructure.api.dependencies import get_auth_service
from infrastructure.api.schemas.auth_schemas import LoginRequest, TokenResponse
from infrastructure.api.schemas.user_schemas import UserResponse
from infrastructure.api.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return TokenResponse(access_token=service.login(payload.username, payload.password))


@router.get("/me", response_model=UserResponse)
def read_current_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
