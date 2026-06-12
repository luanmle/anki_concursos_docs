from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limit_login_attempts
from app.core.security import (
    create_access_token,
    require_admin,
    require_authenticated_user,
)
from app.models import User
from app.repositories import UserRepository
from app.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
)
from app.services import AuthService
from app.services.auth import user_response

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
    dependencies=[Depends(require_admin)],
)


def get_auth_service(session: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(session))


@router.post("/token", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    _rate_limit: None = Depends(limit_login_attempts),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    user = service.authenticate(payload.email, payload.password)
    access_token, expires_in = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=user_response(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user: User = Depends(require_authenticated_user),
) -> UserResponse:
    return user_response(user)


@admin_router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreateRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return user_response(service.create_user(payload))
