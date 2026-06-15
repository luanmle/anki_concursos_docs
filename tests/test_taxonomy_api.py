from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Discipline, Topic


def test_taxonomy_lists_disciplines_and_topics_in_name_order(
    session: Session,
    client: TestClient,
) -> None:
    second = Discipline(name="Zoologia")
    first = Discipline(name="Administracao")
    session.add_all([second, first])
    session.flush()
    session.add_all(
        [
            Topic(discipline_id=first.id, name="Gestao"),
            Topic(discipline_id=first.id, name="Atendimento"),
        ]
    )
    session.commit()

    disciplines = client.get("/disciplines")
    topics = client.get(f"/disciplines/{first.id}/topics")

    assert disciplines.status_code == 200
    assert [item["name"] for item in disciplines.json()["items"]] == [
        "Administracao",
        "Zoologia",
    ]
    assert topics.status_code == 200
    assert topics.json()["discipline"]["discipline_id"] == str(first.id)
    assert [item["name"] for item in topics.json()["items"]] == [
        "Atendimento",
        "Gestao",
    ]


def test_taxonomy_rejects_unknown_discipline(
    client: TestClient,
) -> None:
    response = client.get(
        "/disciplines/00000000-0000-0000-0000-000000000001/topics"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Discipline not found"}


def test_taxonomy_requires_staff_authentication() -> None:
    response = TestClient(app).get("/disciplines")

    assert response.status_code == 401
