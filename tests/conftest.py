import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.rate_limit import reset_rate_limits
from app.main import app
from app.models import Base


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db_session:
        yield db_session
    engine.dispose()


@pytest.fixture
def client(session: Session) -> TestClient:
    def override_get_db():
        with Session(session.get_bind(), expire_on_commit=False) as request_session:
            yield request_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(
            app,
            headers={"X-Admin-API-Key": "development-admin-key"},
        )
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_rate_limits() -> None:
    reset_rate_limits()
