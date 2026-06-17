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
                "role": "student",
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
                "role": "student",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["role"] == "student"


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


def test_student_can_authenticate_but_cannot_use_staff_routes(
    session: Session,
) -> None:
    student = authenticated_client(
        session,
        email="student@example.com",
        role=UserRole.STUDENT,
    )
    try:
        me = student.get("/auth/me")
        cards = student.get("/cards")
        create_card = student.post("/cards", json={})
        users = student.get("/admin/users")
    finally:
        app.dependency_overrides.clear()

    assert me.status_code == 200
    assert me.json()["role"] == "student"
    assert cards.status_code == 403
    assert create_card.status_code == 403
    assert users.status_code == 403


def test_admin_can_list_and_update_users(session: Session) -> None:
    admin = authenticated_client(
        session,
        email="management-admin@example.com",
        role=UserRole.ADMIN,
    )
    managed = create_user(
        session,
        email="managed@example.com",
        role=UserRole.REVIEWER,
    )
    try:
        listed = admin.get("/admin/users", params={"page_size": 1})
        updated = admin.patch(
            f"/admin/users/{managed.id}",
            json={"role": "curator", "is_active": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert listed.json()["pages"] == 2
    assert updated.status_code == 200
    assert updated.json()["role"] == "curator"
    assert updated.json()["is_active"] is False
    session.refresh(managed)
    assert managed.credential_version == 2


def test_password_reset_revokes_existing_token(session: Session) -> None:
    admin = authenticated_client(
        session,
        email="password-admin@example.com",
        role=UserRole.ADMIN,
    )
    managed_client = authenticated_client(
        session,
        email="password-user@example.com",
        role=UserRole.REVIEWER,
    )
    managed = session.query(User).filter_by(
        email="password-user@example.com"
    ).one()
    try:
        reset = admin.post(
            f"/admin/users/{managed.id}/reset-password",
            json={"password": "new-strong-password"},
        )
        revoked = managed_client.get("/auth/me")
        relogin = TestClient(app).post(
            "/auth/token",
            json={
                "email": managed.email,
                "password": "new-strong-password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert reset.status_code == 200
    assert revoked.status_code == 401
    assert revoked.json() == {"detail": "Access token has been revoked"}
    assert relogin.status_code == 200


def test_last_active_admin_cannot_be_demoted(session: Session) -> None:
    admin = authenticated_client(
        session,
        email="last-admin@example.com",
        role=UserRole.ADMIN,
    )
    user = session.query(User).filter_by(email="last-admin@example.com").one()
    try:
        response = admin.patch(
            f"/admin/users/{user.id}",
            json={"role": "reviewer"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "At least one active administrator is required"
    }


def test_admin_can_be_demoted_when_another_active_admin_exists(
    session: Session,
) -> None:
    acting = authenticated_client(
        session,
        email="acting-admin@example.com",
        role=UserRole.ADMIN,
    )
    managed = create_user(
        session,
        email="managed-admin@example.com",
        role=UserRole.ADMIN,
    )
    try:
        response = acting.patch(
            f"/admin/users/{managed.id}",
            json={"role": "reviewer"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["role"] == "reviewer"
