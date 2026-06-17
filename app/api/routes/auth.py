import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limit_login_attempts
from app.core.security import (
    AuthPrincipal,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    require_admin,
    require_authenticated_user,
)
from app.models import User
from app.repositories import UserRepository
from app.schemas import (
    LoginRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
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


def get_auth_service(
    session: Session = Depends(get_db, use_cache=False),
) -> AuthService:
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
        refresh_token=create_refresh_token(user),
        user=user_response(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    token_payload = decode_refresh_token(payload.refresh_token)
    try:
        user_id = uuid.UUID(str(token_payload["sub"]))
        token_version = int(token_payload["ver"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = service.get_user(user_id)
    if token_version != user.credential_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token, expires_in = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=create_refresh_token(user),
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
