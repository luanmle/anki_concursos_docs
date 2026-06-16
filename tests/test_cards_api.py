from hashlib import sha256
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models import Card, CardVersion, Discipline, Topic
from app.models.enums import CardStatus, CardVersionStatus


def test_get_card_by_public_id(session: Session) -> None:
    discipline = Discipline(name="Direito Previdenciario")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Beneficios")
    session.add(topic)
    session.flush()
    card = Card(
        public_id="AC-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        canonical_key="retirement-benefit",
        discipline_id=discipline.id,
        topic_id=topic.id,
        status=CardStatus.PUBLISHED,
    )
    session.add(card)
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="O que e aposentadoria?",
        back_text="Um beneficio previdenciario.",
        answer_text="Beneficio previdenciario.",
        explanation_text="E concedido quando os requisitos sao atendidos.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"retirement-benefit-v1").hexdigest(),
    )
    session.add(version)
    session.flush()
    card.current_version_id = version.id
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get(
            "/cards/public/ac-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["public_id"] == card.public_id
    assert response.json()["card_id"] == str(card.id)
    assert response.json()["current_version"]["card_version_id"] == str(version.id)


def test_get_card_by_unknown_public_id_returns_404(session: Session) -> None:
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get(
            "/cards/public/AC-BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Card not found"}


def test_public_lookup_does_not_expose_unpublished_card(
    session: Session,
) -> None:
    discipline = Discipline(name="Direito Eleitoral")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Eleicoes")
    session.add(topic)
    session.flush()
    card = Card(
        public_id="AC-CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
        canonical_key="unpublished-election-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
        status=CardStatus.NEEDS_REVIEW,
    )
    session.add(card)
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    try:
        response = TestClient(app).get(f"/cards/public/{card.public_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_card_creation_requires_admin_api_key() -> None:
    response = TestClient(app).post("/cards", json={})

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing authentication credentials"
    }


def create_taxonomy(session: Session, suffix: str) -> tuple[Discipline, Topic]:
    discipline = Discipline(name=f"Disciplina {suffix}")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name=f"Assunto {suffix}")
    session.add(topic)
    session.commit()
    return discipline, topic


def card_payload(
    discipline: Discipline,
    topic: Topic,
    *,
    canonical_key: str,
) -> dict[str, str]:
    return {
        "canonical_key": canonical_key,
        "discipline_id": str(discipline.id),
        "topic_id": str(topic.id),
        "front_text": "Qual e a pergunta?",
        "back_text": "Este e o verso.",
        "answer_text": "Esta e a resposta.",
        "explanation_text": "Esta e a explicacao.",
        "change_reason": "Versao inicial",
        "created_by": "api-test",
    }


def test_create_card_with_version_one(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Criacao")

    response = client.post(
        "/cards",
        json=card_payload(
            discipline,
            topic,
            canonical_key="create-card-version-one",
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["public_id"].startswith("AC-")
    assert body["status"] == "needs_review"
    assert body["current_version"]["version_number"] == 1
    assert body["current_version"]["status"] == "needs_review"
    assert len(body["current_version"]["content_hash"]) == 64
    assert len(body["versions"]) == 1

    card = session.get(Card, uuid.UUID(body["card_id"]))
    assert card is not None
    assert card.current_version_id == uuid.UUID(
        body["current_version"]["card_version_id"]
    )


def test_create_card_rejects_topic_from_another_discipline(
    session: Session, client: TestClient
) -> None:
    discipline, _ = create_taxonomy(session, "Taxonomia A")
    _, other_topic = create_taxonomy(session, "Taxonomia B")

    response = client.post(
        "/cards",
        json=card_payload(
            discipline,
            other_topic,
            canonical_key="invalid-taxonomy-api",
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Topic does not belong to the informed discipline"
    )
    assert session.scalar(select(func.count()).select_from(Card)) == 0


def test_create_card_rejects_duplicate_canonical_key(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Duplicidade")
    payload = card_payload(
        discipline,
        topic,
        canonical_key="duplicate-canonical-key",
    )

    assert client.post("/cards", json=payload).status_code == 201
    response = client.post("/cards", json=payload)

    assert response.status_code == 409
    assert response.json() == {"detail": "canonical_key already exists"}


def test_list_cards_supports_pagination_and_filters(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Listagem")
    for index in range(3):
        response = client.post(
            "/cards",
            json=card_payload(
                discipline,
                topic,
                canonical_key=f"list-card-{index}",
            ),
        )
        assert response.status_code == 201

    response = client.get(
        "/cards",
        params={
            "page": 2,
            "page_size": 2,
            "discipline_id": str(discipline.id),
            "topic_id": str(topic.id),
            "status": "needs_review",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total"] == 3
    assert body["pages"] == 2
    assert len(body["items"]) == 1

    public_id = body["items"][0]["public_id"]
    filtered = client.get("/cards", params={"public_id": public_id.lower()})
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["public_id"] == public_id


def test_create_new_version_preserves_current_and_history(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Versionamento")
    created = client.post(
        "/cards",
        json=card_payload(
            discipline,
            topic,
            canonical_key="versioned-card-api",
        ),
    )
    assert created.status_code == 201
    card_id = created.json()["card_id"]
    public_id = created.json()["public_id"]
    version_one_id = created.json()["current_version"]["card_version_id"]

    new_version = client.post(
        f"/cards/{card_id}/versions",
        json={
            "front_text": "Qual e a pergunta revisada?",
            "back_text": "Este e o verso revisado.",
            "answer_text": "Esta e a resposta revisada.",
            "explanation_text": "Esta e a explicacao revisada.",
            "change_reason": "Melhoria pedagogica",
            "created_by": "api-test",
        },
    )

    assert new_version.status_code == 201
    assert new_version.json()["version_number"] == 2
    assert new_version.json()["status"] == "needs_review"

    detail = client.get(f"/cards/{card_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["public_id"] == public_id
    assert body["current_version"]["card_version_id"] == version_one_id
    assert [version["version_number"] for version in body["versions"]] == [2, 1]


def test_create_identical_version_returns_conflict(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Versao Duplicada")
    payload = card_payload(
        discipline,
        topic,
        canonical_key="identical-version-api",
    )
    created = client.post("/cards", json=payload)
    card_id = created.json()["card_id"]

    response = client.post(
        f"/cards/{card_id}/versions",
        json={
            "front_text": payload["front_text"],
            "back_text": payload["back_text"],
            "answer_text": payload["answer_text"],
            "explanation_text": payload["explanation_text"],
            "change_reason": "Sem mudanca real",
            "created_by": "api-test",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "An identical card version already exists"}


def csv_import_client(session: Session) -> TestClient:
    def override_get_db():
        with Session(session.get_bind(), expire_on_commit=False) as request_session:
            yield request_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(
        app,
        headers={"X-Admin-API-Key": "development-admin-key"},
    )


def test_import_csv_creates_cards_with_generated_identifiers(
    session: Session,
) -> None:
    discipline, topic = create_taxonomy(session, "Importacao CSV")
    csv_text = "\n".join(
        [
            "discipline,topic,front_text,back_text,answer_text,explanation_text,tags",
            (
                f"{discipline.name},{topic.name},Pergunta importada,"
                "Verso importado,Resposta importada,Explicacao importada,"
                "tag_importada"
            ),
        ]
    )

    client = csv_import_client(session)
    try:
        response = client.post(
            "/card-imports/csv",
            json={"csv_text": csv_text},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 1
    assert body["created"] == 1
    assert body["duplicates"] == 0
    assert body["errors"] == 0
    item = body["items"][0]
    assert item["status"] == "created"
    assert item["public_id"].startswith("AC-")
    assert item["card_id"]
    assert item["card_version_id"]

    card = session.get(Card, uuid.UUID(item["card_id"]))
    assert card is not None
    assert card.public_id == item["public_id"]
    assert card.canonical_key.startswith("csv-")
    assert card.status == CardStatus.NEEDS_REVIEW
    assert card.current_version is not None
    assert card.current_version.status == CardVersionStatus.NEEDS_REVIEW
    assert card.current_version.version_number == 1


def test_import_csv_reports_duplicates_without_creating_second_card(
    session: Session,
) -> None:
    discipline, topic = create_taxonomy(session, "Importacao Duplicada")
    csv_text = "\n".join(
        [
            "discipline,topic,front_text,back_text,answer_text,explanation_text",
            (
                f"{discipline.name},{topic.name},Pergunta duplicada,"
                "Verso,Resposta,Explicacao"
            ),
            (
                f"{discipline.name},{topic.name},Pergunta duplicada,"
                "Verso,Resposta,Explicacao"
            ),
        ]
    )

    client = csv_import_client(session)
    try:
        response = client.post("/card-imports/csv", json={"csv_text": csv_text})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 2
    assert body["created"] == 1
    assert body["duplicates"] == 1
    assert body["errors"] == 0
    assert [item["status"] for item in body["items"]] == ["created", "duplicate"]
    assert session.scalar(select(func.count()).select_from(Card)) == 1


def test_import_csv_dry_run_validates_without_persisting(
    session: Session,
) -> None:
    discipline, topic = create_taxonomy(session, "Importacao Dry Run")
    csv_text = "\n".join(
        [
            "discipline_id,topic_id,front_text,back_text,answer_text,explanation_text",
            (
                f"{discipline.id},{topic.id},Pergunta valida,"
                "Verso,Resposta,Explicacao"
            ),
            (
                f"{discipline.id},{topic.id},,"
                "Verso sem frente,Resposta,Explicacao"
            ),
        ]
    )

    client = csv_import_client(session)
    try:
        response = client.post(
            "/card-imports/csv",
            json={"csv_text": csv_text, "dry_run": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["created"] == 1
    assert body["errors"] == 1
    assert [item["status"] for item in body["items"]] == ["ready", "error"]
    assert session.scalar(select(func.count()).select_from(Card)) == 0
