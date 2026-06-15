from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.models import CardVersion, Discipline, Topic


def create_taxonomy(session: Session, suffix: str) -> tuple[Discipline, Topic]:
    discipline = Discipline(name=f"Disciplina Report {suffix}")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name=f"Assunto Report {suffix}")
    session.add(topic)
    session.commit()
    return discipline, topic


def create_published_card(
    session: Session,
    client: TestClient,
    suffix: str,
) -> dict:
    discipline, topic = create_taxonomy(session, suffix)
    created = client.post(
        "/cards",
        json={
            "canonical_key": f"report-card-{suffix}",
            "discipline_id": str(discipline.id),
            "topic_id": str(topic.id),
            "front_text": f"Frente original {suffix}",
            "back_text": f"Verso original {suffix}",
            "answer_text": f"Resposta original {suffix}",
            "explanation_text": f"Explicacao original {suffix}",
            "change_reason": "Versao inicial",
            "created_by": "report-test",
        },
    )
    assert created.status_code == 201
    card = created.json()
    version_id = card["current_version"]["card_version_id"]
    assert client.post(
        f"/cards/{card['card_id']}/versions/{version_id}/approve"
    ).status_code == 200
    published = client.post(
        f"/cards/{card['card_id']}/versions/{version_id}/publish"
    )
    assert published.status_code == 200
    return published.json()


def report_payload(card: dict, *, report_type: str = "wrong_answer") -> dict:
    return {
        "card_id": card["card_id"],
        "card_version_id": card["current_version"]["card_version_id"],
        "reporter_reference": "user-123",
        "report_type": report_type,
        "message": "O conteudo precisa de revisao.",
    }


def test_public_user_can_report_published_card_version(
    session: Session, client: TestClient
) -> None:
    card = create_published_card(session, client, "Publico")

    response = TestClient(app).post("/reports", json=report_payload(card))

    assert response.status_code == 201
    body = response.json()
    assert body["card_id"] == card["card_id"]
    assert body["public_id"] == card["public_id"]
    assert body["card_version_id"] == card["current_version"][
        "card_version_id"
    ]
    assert body["status"] == "open"
    assert body["reporter_reference"] == "user-123"
    assert body["review_task"]["status"] == "pending"
    assert body["review_task"]["decision"] is None


def test_report_rejects_unpublished_version(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Nao Publicado")
    created = client.post(
        "/cards",
        json={
            "canonical_key": "unpublished-report-card",
            "discipline_id": str(discipline.id),
            "topic_id": str(topic.id),
            "front_text": "Frente",
            "back_text": "Verso",
            "answer_text": "Resposta",
            "explanation_text": "Explicacao",
            "change_reason": "Versao inicial",
            "created_by": "report-test",
        },
    ).json()

    response = TestClient(app).post(
        "/reports",
        json=report_payload(created),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Published card version not found"
    }


def test_rejected_report_preserves_card_content(
    session: Session, client: TestClient
) -> None:
    card = create_published_card(session, client, "Rejeitado")
    report = client.post("/reports", json=report_payload(card)).json()
    version_count_before = session.scalar(
        select(func.count()).select_from(CardVersion)
    )

    reviewed = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json={
            "decision": "rejected",
            "reviewed_by": "admin@example.com",
            "admin_comment": "O conteudo publicado esta correto.",
        },
    )

    assert reviewed.status_code == 200
    body = reviewed.json()
    assert body["status"] == "rejected"
    assert body["review_task"]["status"] == "completed"
    assert body["review_task"]["decision"] == "rejected"
    assert body["review_task"]["resulting_card_version_id"] is None
    assert (
        session.scalar(select(func.count()).select_from(CardVersion))
        == version_count_before
    )
    detail = client.get(f"/cards/{card['card_id']}").json()
    assert detail["current_version"]["card_version_id"] == card[
        "current_version"
    ]["card_version_id"]
    assert len(detail["versions"]) == 1


def test_approved_correction_creates_review_version_and_preserves_published(
    session: Session, client: TestClient
) -> None:
    card = create_published_card(session, client, "Conversao")
    original_version_id = card["current_version"]["card_version_id"]
    report = client.post(
        "/reports",
        json=report_payload(card, report_type="bad_explanation"),
    ).json()

    reviewed = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json={
            "decision": "converted_to_new_version",
            "reviewed_by": "curator@example.com",
            "admin_comment": "Correcao aceita para nova revisao.",
            "proposed_version": {
                "front_text": "Frente corrigida",
                "back_text": "Verso corrigido",
                "answer_text": "Resposta corrigida",
                "explanation_text": "Explicacao corrigida",
                "change_reason": "Correcao do report",
            },
        },
    )

    assert reviewed.status_code == 200
    body = reviewed.json()
    resulting_version_id = body["review_task"][
        "resulting_card_version_id"
    ]
    assert body["status"] == "resolved"
    assert body["review_task"]["decision"] == "converted_to_new_version"
    assert resulting_version_id is not None

    detail = client.get(f"/cards/{card['card_id']}").json()
    assert detail["public_id"] == card["public_id"]
    assert detail["status"] == "published"
    assert detail["current_version"]["card_version_id"] == original_version_id
    assert [version["version_number"] for version in detail["versions"]] == [
        2,
        1,
    ]
    new_version = detail["versions"][0]
    assert new_version["card_version_id"] == resulting_version_id
    assert new_version["status"] == "needs_review"
    assert new_version["change_reason"] == "Correcao do report"
    original_version = detail["versions"][1]
    assert original_version["card_version_id"] == original_version_id
    assert original_version["front_text"].startswith("Frente original")

    public_card = client.get(f"/cards/public/{card['public_id']}").json()
    assert (
        public_card["current_version"]["card_version_id"]
        == original_version_id
    )

    repeated = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json={
            "decision": "rejected",
            "reviewed_by": "curator@example.com",
            "admin_comment": "Tentativa posterior.",
        },
    )
    assert repeated.status_code == 409
    assert repeated.json() == {
        "detail": "Report has already been reviewed"
    }


def test_admin_report_list_supports_filters_and_requires_auth(
    session: Session, client: TestClient
) -> None:
    card = create_published_card(session, client, "Lista")
    first = client.post(
        "/reports",
        json=report_payload(card, report_type="typo"),
    ).json()
    second = client.post(
        "/reports",
        json=report_payload(card, report_type="suggestion"),
    ).json()
    assert client.post(
        f"/admin/reports/{first['report_id']}/review",
        json={
            "decision": "duplicate",
            "reviewed_by": "admin@example.com",
            "admin_comment": "Mesmo apontamento ja registrado.",
        },
    ).status_code == 200

    filtered = client.get(
        "/admin/reports",
        params={"status": "open", "report_type": "suggestion"},
    )

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["report_id"] == second["report_id"]

    unauthorized = TestClient(app).get("/admin/reports")
    assert unauthorized.status_code == 401


def test_review_payload_enforces_version_conversion_contract(
    session: Session, client: TestClient
) -> None:
    card = create_published_card(session, client, "Contrato")
    report = client.post("/reports", json=report_payload(card)).json()

    missing_version = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json={
            "decision": "converted_to_new_version",
            "reviewed_by": "admin@example.com",
            "admin_comment": "Precisa de nova versao.",
        },
    )
    unexpected_version = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json={
            "decision": "rejected",
            "reviewed_by": "admin@example.com",
            "admin_comment": "Nao procede.",
            "proposed_version": {
                "front_text": "Frente",
                "back_text": "Verso",
                "answer_text": "Resposta",
                "explanation_text": "Explicacao",
                "change_reason": "Nao permitido",
            },
        },
    )

    assert missing_version.status_code == 422
    assert unexpected_version.status_code == 422


def test_outdated_law_conversion_requires_evidence_review(
    session: Session, client: TestClient
) -> None:
    card = create_published_card(session, client, "Lei Desatualizada")
    report = client.post(
        "/reports",
        json=report_payload(card, report_type="outdated_law"),
    ).json()
    review_payload = {
        "decision": "converted_to_new_version",
        "reviewed_by": "legal-curator@example.com",
        "admin_comment": "A norma aplicavel foi conferida.",
        "proposed_version": {
            "front_text": "Frente juridica atualizada",
            "back_text": "Verso juridico atualizado",
            "answer_text": "Resposta juridica atualizada",
            "explanation_text": "Explicacao juridica atualizada",
            "change_reason": "Atualizacao legislativa",
        },
    }

    missing_evidence = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json=review_payload,
    )

    assert missing_evidence.status_code == 409
    assert missing_evidence.json() == {
        "detail": (
            "Outdated law reports require evidence review before conversion"
        )
    }

    reviewed = client.post(
        f"/admin/reports/{report['report_id']}/review",
        json={**review_payload, "evidence_reviewed": True},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_task"]["evidence_reviewed"] is True
