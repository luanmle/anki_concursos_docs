from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.main import app
from app.models import User
from app.models.enums import UserRole


def create_user(
    session: Session,
    *,
    email: str,
    role: UserRole,
    password: str = "strong-test-password",
) -> User:
    user = User(
        email=email,
        display_name=email.split("@", 1)[0],
        password_hash=hash_password(password),
        role=role,
    )
    session.add(user)
    session.commit()
    return user


def authenticated_client(
    session: Session,
    *,
    email: str,
    role: UserRole,
) -> TestClient:
    create_user(session, email=email, role=role)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    login = TestClient(app).post(
        "/auth/token",
        json={"email": email, "password": "strong-test-password"},
    )
    assert login.status_code == 200
    return TestClient(
        app,
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("same-password")
    second = hash_password("same-password")

    assert first != second
    assert verify_password("same-password", first)
    assert not verify_password("wrong-password", first)


def test_login_and_me_return_authenticated_user(session: Session) -> None:
    client = authenticated_client(
        session,
        email="admin@example.com",
        role=UserRole.ADMIN,
    )
    try:
        response = client.get("/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"
    assert response.json()["role"] == "admin"


def test_invalid_login_is_rejected(session: Session) -> None:
    create_user(
        session,
        email="reviewer@example.com",
        role=UserRole.REVIEWER,
    )
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).post(
            "/auth/token",
            json={
                "email": "reviewer@example.com",
                "password": "incorrect-password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_only_admin_can_create_users(session: Session) -> None:
    curator = authenticated_client(
        session,
        email="curator@example.com",
        role=UserRole.CURATOR,
    )
    try:
        forbidden = curator.post(
            "/admin/users",
            json={
                "email": "new@example.com",
                "display_name": "New user",
                "password": "another-strong-password",
                "role": "reviewer",
            },
        )
    finally:
        app.dependency_overrides.clear()
    assert forbidden.status_code == 403

    admin = authenticated_client(
        session,
        email="second-admin@example.com",
        role=UserRole.ADMIN,
    )
    try:
        created = admin.post(
            "/admin/users",
            json={
                "email": "new@example.com",
                "display_name": "New user",
                "password": "another-strong-password",
                "role": "reviewer",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["role"] == "reviewer"


def test_reviewer_cannot_create_cards(session: Session) -> None:
    reviewer = authenticated_client(
        session,
        email="readonly-reviewer@example.com",
        role=UserRole.REVIEWER,
    )
    try:
        response = reviewer.post("/cards", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}
