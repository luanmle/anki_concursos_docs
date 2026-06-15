import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limit_login_attempts
from app.core.security import (
    AuthPrincipal,
    create_access_token,
    require_admin,
    require_authenticated_user,
)
from app.models import User
from app.repositories import UserRepository
from app.schemas import (
    LoginRequest,
    PasswordResetRequest,
    TokenResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
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


@admin_router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AuthService = Depends(get_auth_service),
) -> UserListResponse:
    return service.list_users(page=page, page_size=page_size)


@admin_router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    admin: AuthPrincipal = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return user_response(
        service.update_user(
            user_id,
            payload,
            acting_user_id=admin.user_id,
        )
    )


@admin_router.post("/{user_id}/reset-password", response_model=UserResponse)
def reset_user_password(
    user_id: uuid.UUID,
    payload: PasswordResetRequest,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return user_response(service.reset_password(user_id, payload))
