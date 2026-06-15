from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app


def test_root_identifies_api_and_health_endpoints() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "Anki Concursos API",
        "status": "ok",
        "health": "/health",
        "readiness": "/ready",
    }


def test_health_check() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_database(session: Session) -> None:
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_request_body_limit_rejects_oversized_payload() -> None:
    response = TestClient(app).post(
        "/reports",
        content=b"x" * 262_145,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}
