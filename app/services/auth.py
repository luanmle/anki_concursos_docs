import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import UserCreateRequest, UserResponse


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

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
