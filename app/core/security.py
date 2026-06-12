import base64
import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import User
from app.models.enums import UserRole

PASSWORD_ITERATIONS = 600_000


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: uuid.UUID | None
    email: str
    role: UserRole
    legacy: bool = False


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{_base64url_encode(salt)}${_base64url_encode(digest)}"
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _base64url_decode(salt),
            int(iterations),
        )
        return hmac.compare_digest(_base64url_encode(digest), expected)
    except (TypeError, ValueError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_in = settings.access_token_expire_minutes * 60
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _base64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode()
    )
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_base64url_encode(signature)}", expires_in


def _decode_access_token(token: str) -> dict[str, object]:
    settings = get_settings()
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected = hmac.new(
            settings.auth_secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected, _base64url_decode(encoded_signature)):
            raise ValueError("invalid signature")
        header = json.loads(_base64url_decode(encoded_header))
        payload = json.loads(_base64url_decode(encoded_payload))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("invalid header")
        if int(payload["exp"]) <= int(datetime.now(UTC).timestamp()):
            raise ValueError("expired token")
        return payload
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_authenticated_user(
    authorization: Annotated[str | None, Header()] = None,
    session: Session = Depends(get_db),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_access_token(authorization.removeprefix("Bearer ").strip())
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or unknown user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*allowed_roles: UserRole):
    def dependency(
        authorization: Annotated[str | None, Header()] = None,
        x_admin_api_key: Annotated[str | None, Header()] = None,
        session: Session = Depends(get_db),
    ) -> AuthPrincipal:
        settings = get_settings()
        if authorization is not None and authorization.startswith("Bearer "):
            user = require_authenticated_user(authorization, session)
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            return AuthPrincipal(user.id, user.email, user.role)

        if (
            settings.allow_legacy_admin_api_key
            and x_admin_api_key is not None
            and secrets.compare_digest(x_admin_api_key, settings.admin_api_key)
        ):
            return AuthPrincipal(
                user_id=None,
                email="legacy-admin",
                role=UserRole.ADMIN,
                legacy=True,
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return dependency


require_admin = require_roles(UserRole.ADMIN)
require_curator = require_roles(UserRole.ADMIN, UserRole.CURATOR)
require_reviewer = require_roles(UserRole.ADMIN, UserRole.REVIEWER)
require_staff = require_roles(UserRole.ADMIN, UserRole.CURATOR, UserRole.REVIEWER)

# Temporary compatibility for existing integrations outside production.
require_admin_api_key = require_admin
