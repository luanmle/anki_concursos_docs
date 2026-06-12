import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=1024)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("invalid email address")
        return normalized


class UserCreateRequest(LoginRequest):
    display_name: str = Field(min_length=1, max_length=255)
    role: UserRole

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UserResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
