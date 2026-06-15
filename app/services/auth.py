import math
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models import User
from app.models.enums import UserRole
from app.repositories.users import UserRepository
from app.schemas.auth import (
    PasswordResetRequest,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def authenticate(self, email: str, password: str) -> User:
        user = self.repository.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user.last_login_at = datetime.now(UTC)
        self.repository.commit()
        return user

    def create_user(self, payload: UserCreateRequest) -> User:
        user = User(
            email=payload.email,
            display_name=payload.display_name,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        try:
            self.repository.add(user)
            self.repository.commit()
        except IntegrityError as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email already exists",
            ) from exc
        return user

    def list_users(self, *, page: int, page_size: int) -> UserListResponse:
        users, total = self.repository.list_users(page=page, page_size=page_size)
        return UserListResponse(
            items=[user_response(user) for user in users],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def update_user(
        self,
        user_id: uuid.UUID,
        payload: UserUpdateRequest,
        *,
        acting_user_id: uuid.UUID | None,
    ) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            self._raise_user_not_found()
        if user.id == acting_user_id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Administrators cannot deactivate their own account",
            )
        removes_active_admin = (
            user.role == UserRole.ADMIN
            and user.is_active
            and (
                payload.role not in (None, UserRole.ADMIN)
                or payload.is_active is False
            )
        )
        if removes_active_admin:
            active_admins = self.repository.lock_active_admins()
            locked_user = next(
                (admin for admin in active_admins if admin.id == user_id),
                None,
            )
            if locked_user is not None:
                user = locked_user
                if len(active_admins) <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="At least one active administrator is required",
                    )
            else:
                user = self.repository.get_by_id(user_id, for_update=True)
                if user is None:
                    self._raise_user_not_found()
        else:
            user = self.repository.get_by_id(user_id, for_update=True)
            if user is None:
                self._raise_user_not_found()

        security_changed = False
        if payload.display_name is not None:
            user.display_name = payload.display_name
        if payload.role is not None and payload.role != user.role:
            user.role = payload.role
            security_changed = True
        if payload.is_active is not None and payload.is_active != user.is_active:
            user.is_active = payload.is_active
            security_changed = True
        if security_changed:
            user.credential_version += 1
        self.repository.commit()
        return user

    def reset_password(
        self,
        user_id: uuid.UUID,
        payload: PasswordResetRequest,
    ) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            self._raise_user_not_found()
        user.password_hash = hash_password(payload.password)
        user.credential_version += 1
        self.repository.commit()
        return user

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    def _raise_user_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
