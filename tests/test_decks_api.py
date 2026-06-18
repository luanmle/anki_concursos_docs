import csv
import hashlib
import io
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Discipline, Topic, User
from app.models.enums import UserRole


def create_taxonomy(session: Session, suffix: str) -> tuple[Discipline, Topic]:
    discipline = Discipline(name=f"Disciplina Deck {suffix}")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name=f"Assunto Deck {suffix}")
    session.add(topic)
    session.commit()
    return discipline, topic


def create_bearer_client(session: Session) -> TestClient:
    user = User(
        email=f"subscriber-{uuid.uuid4().hex}@example.com",
        display_name="Subscriber",
        password_hash=hash_password("subscriber-password"),
        role=UserRole.STUDENT,
    )
    session.add(user)
    session.commit()
    token, _expires_in = create_access_token(user)

    def override_get_db():
        with Session(session.get_bind(), expire_on_commit=False) as request_session:
            yield request_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def create_curator_client(session: Session) -> TestClient:
    user = User(
        email=f"curator-{uuid.uuid4().hex}@example.com",
        display_name="Curator",
        password_hash=hash_password("curator-password"),
        role=UserRole.ADMIN,
    )
    session.add(user)
    session.commit()
    token, _expires_in = create_access_token(user)

    def override_get_db():
        with Session(session.get_bind(), expire_on_commit=False) as request_session:
            yield request_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def create_card(
    client: TestClient,
    discipline: Discipline,
    topic: Topic,
    canonical_key: str,
    *,
    card_kind: str = "basic",
    front_text: str | None = None,
) -> dict:
    response = client.post(
        "/cards",
        json={
            "card_kind": card_kind,
            "canonical_key": canonical_key,
            "discipline_id": str(discipline.id),
            "topic_id": str(topic.id),
            "front_text": front_text or f"Frente {canonical_key}",
            "back_text": f"Verso {canonical_key}",
            "answer_text": f"Resposta {canonical_key}",
            "explanation_text": f"Explicacao {canonical_key}",
            "change_reason": "Versao inicial",
            "created_by": "deck-test",
        },
    )
    assert response.status_code == 201
    return response.json()


def approve_and_publish(client: TestClient, card: dict) -> dict:
    card_id = card["card_id"]
    version_id = card["current_version"]["card_version_id"]
    approved = client.post(
        f"/cards/{card_id}/versions/{version_id}/approve"
    )
    assert approved.status_code == 200
    published = client.post(
        f"/cards/{card_id}/versions/{version_id}/publish"
    )
    assert published.status_code == 200
    return published.json()


def create_deck(
    client: TestClient,
    discipline: Discipline,
    name: str,
) -> dict:
    response = client.post(
        "/decks",
        json={
            "name": name,
            "discipline_id": str(discipline.id),
            "description": "Deck de teste",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_and_publish_new_version(
    client: TestClient,
    card: dict,
    suffix: str,
) -> str:
    version = client.post(
        f"/cards/{card['card_id']}/versions",
        json={
            "front_text": f"Frente revisada {suffix}",
            "back_text": f"Verso revisado {suffix}",
            "answer_text": f"Resposta revisada {suffix}",
            "explanation_text": f"Explicacao revisada {suffix}",
            "change_reason": f"Atualizacao {suffix}",
            "created_by": "deck-test",
        },
    )
    assert version.status_code == 201
    version_id = version.json()["card_version_id"]
    assert client.post(
        f"/cards/{card['card_id']}/versions/{version_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/cards/{card['card_id']}/versions/{version_id}/publish"
    ).status_code == 200
    return version_id


def test_publish_requires_approved_version(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Aprovacao")
    card = create_card(client, discipline, topic, "publish-needs-approval")

    response = client.post(
        f"/cards/{card['card_id']}/versions/"
        f"{card['current_version']['card_version_id']}/publish"
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only an approved version can be published"
    }


def test_approve_and_publish_makes_card_public(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Publicacao")
    card = create_card(client, discipline, topic, "approved-published-card")

    published = approve_and_publish(client, card)

    assert published["status"] == "published"
    assert published["current_version"]["status"] == "published"
    public_response = client.get(f"/cards/public/{published['public_id']}")
    assert public_response.status_code == 200


def test_new_draft_does_not_hide_published_current_version(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Rascunho")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "published-with-draft"),
    )

    draft = client.post(
        f"/cards/{card['card_id']}/versions",
        json={
            "front_text": "Nova frente ainda em revisao",
            "back_text": "Novo verso",
            "answer_text": "Nova resposta",
            "explanation_text": "Nova explicacao",
            "change_reason": "Proposta de melhoria",
            "created_by": "deck-test",
        },
    )

    assert draft.status_code == 201
    public_response = client.get(f"/cards/public/{card['public_id']}")
    assert public_response.status_code == 200
    assert (
        public_response.json()["current_version"]["card_version_id"]
        == card["current_version"]["card_version_id"]
    )


def test_deck_rejects_unpublished_card(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Nao Publicado")
    card = create_card(client, discipline, topic, "unpublished-deck-card")
    deck = create_deck(client, discipline, "Deck Nao Publicado")

    response = client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only the current published card version can be added"
    }


def test_release_tracks_added_and_updated_cards(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Update")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "release-updated-card"),
    )
    deck = create_deck(client, discipline, "Deck Update")

    added = client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    )
    assert added.status_code == 200
    first_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Primeira release"},
    )
    assert first_release.status_code == 201
    assert first_release.json()["release_number"] == 1
    assert [item["action"] for item in first_release.json()["items"]] == ["added"]

    version_two = client.post(
        f"/cards/{card['card_id']}/versions",
        json={
            "front_text": "Frente revisada",
            "back_text": "Verso revisado",
            "answer_text": "Resposta revisada",
            "explanation_text": "Explicacao revisada",
            "change_reason": "Atualizacao",
            "created_by": "deck-test",
        },
    )
    assert version_two.status_code == 201
    version_two_id = version_two.json()["card_version_id"]
    assert client.post(
        f"/cards/{card['card_id']}/versions/{version_two_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/cards/{card['card_id']}/versions/{version_two_id}/publish"
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200

    second_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Segunda release"},
    )

    assert second_release.status_code == 201
    assert second_release.json()["release_number"] == 2
    assert second_release.json()["items"] == [
        {
            "action": "updated",
            "card_id": card["card_id"],
            "public_id": card["public_id"],
            "card_version_id": version_two_id,
        }
    ]


def test_release_tracks_removed_and_deprecated_cards(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Remocao")
    removed_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "removed-release-card"),
    )
    deprecated_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "deprecated-release-card"),
    )
    deck = create_deck(client, discipline, "Deck Remocao")
    for card in (removed_card, deprecated_card):
        assert client.post(
            f"/decks/{deck['deck_id']}/cards",
            json={"card_id": card["card_id"]},
        ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).status_code == 201

    assert client.post(
        f"/decks/{deck['deck_id']}/cards/{removed_card['card_id']}/remove",
        json={"action": "removed"},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards/{deprecated_card['card_id']}/remove",
        json={"action": "deprecated"},
    ).status_code == 200

    release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Remocoes"},
    )

    assert release.status_code == 201
    actions = {
        item["card_id"]: item["action"] for item in release.json()["items"]
    }
    assert actions == {
        removed_card["card_id"]: "removed",
        deprecated_card["card_id"]: "deprecated",
    }


def test_release_without_changes_returns_conflict(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Sem Mudancas")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "no-release-changes-card"),
    )
    deck = create_deck(client, discipline, "Deck Sem Mudancas")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).status_code == 201

    response = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Deck has no unpublished changes"}


def test_release_csv_is_utf8_escaped_configurable_and_deterministic(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "CSV")
    card_response = client.post(
        "/cards",
        json={
            "canonical_key": "csv-special-content",
            "discipline_id": str(discipline.id),
            "topic_id": str(topic.id),
            "front_text": 'O que significa "ação"?\nExplique, brevemente.',
            "back_text": "É um conteúdo; com delimitadores.",
            "answer_text": "Ação pública",
            "explanation_text": "Preserva acentos, aspas e\nquebras de linha.",
            "change_reason": "Versão inicial",
            "created_by": "csv-test",
        },
    )
    assert card_response.status_code == 201
    card = approve_and_publish(client, card_response.json())
    deck = create_deck(client, discipline, "Deck CSV")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    release_response = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Release CSV"},
    )
    assert release_response.status_code == 201
    release = release_response.json()
    export_url = (
        f"/decks/{deck['deck_id']}/releases/"
        f"{release['release_id']}/export.csv"
    )

    first = client.get(export_url)
    second = client.get(export_url)

    assert first.status_code == 200
    assert first.content == second.content
    assert first.headers["x-content-sha256"] == hashlib.sha256(
        first.content
    ).hexdigest()
    assert first.headers["x-row-count"] == "1"
    assert first.headers["x-release-number"] == "1"
    assert (
        first.headers["content-disposition"]
        == f'attachment; filename="deck-{deck["deck_id"]}-release-1.csv"'
    )
    rows = list(
        csv.DictReader(io.StringIO(first.content.decode("utf-8")))
    )
    assert rows == [
        {
            "public_id": card["public_id"],
            "card_id": card["card_id"],
            "card_version_id": card["current_version"]["card_version_id"],
            "card_kind": "basic",
            "note_type": "Anki Concursos Basic",
            "front_text": 'O que significa "ação"?\nExplique, brevemente.',
            "back_text": "É um conteúdo; com delimitadores.",
            "answer_text": "Ação pública",
            "explanation_text": "Preserva acentos, aspas e\nquebras de linha.",
            "tags": (
                f"deck::{deck['deck_id']} "
                f"card::{card['public_id']}"
            ),
        }
    ]

    semicolon = client.get(
        export_url,
        params={"delimiter": "semicolon", "include_tags": "false"},
    )
    semicolon_rows = list(
        csv.DictReader(
            io.StringIO(semicolon.content.decode("utf-8")),
            delimiter=";",
        )
    )
    assert semicolon.status_code == 200
    assert semicolon_rows[0]["tags"] == ""
    assert semicolon_rows[0]["front_text"] == rows[0]["front_text"]
    assert semicolon.content != first.content


def test_release_csv_reconstructs_historical_snapshot(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Historico CSV")
    updated_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "csv-historical-update"),
    )
    deprecated_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "csv-historical-deprecated"),
    )
    deck = create_deck(client, discipline, "Deck Historico CSV")
    for card in (updated_card, deprecated_card):
        assert client.post(
            f"/decks/{deck['deck_id']}/cards",
            json={"card_id": card["card_id"]},
        ).status_code == 200
    first_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).json()

    version_two = client.post(
        f"/cards/{updated_card['card_id']}/versions",
        json={
            "front_text": "Frente histórica v2",
            "back_text": "Verso histórico v2",
            "answer_text": "Resposta histórica v2",
            "explanation_text": "Explicação histórica v2",
            "change_reason": "Atualização para v2",
            "created_by": "csv-test",
        },
    ).json()
    version_two_id = version_two["card_version_id"]
    assert client.post(
        f"/cards/{updated_card['card_id']}/versions/{version_two_id}/approve"
    ).status_code == 200
    assert client.post(
        f"/cards/{updated_card['card_id']}/versions/{version_two_id}/publish"
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": updated_card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards/"
        f"{deprecated_card['card_id']}/remove",
        json={"action": "deprecated"},
    ).status_code == 200
    second_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).json()

    def export_rows(release_id: str) -> list[dict[str, str]]:
        response = client.get(
            f"/decks/{deck['deck_id']}/releases/{release_id}/export.csv"
        )
        assert response.status_code == 200
        return list(
            csv.DictReader(io.StringIO(response.content.decode("utf-8")))
        )

    first_rows = export_rows(first_release["release_id"])
    second_rows = export_rows(second_release["release_id"])

    assert [row["public_id"] for row in first_rows] == sorted(
        row["public_id"] for row in first_rows
    )
    first_versions = {
        row["card_id"]: row["card_version_id"] for row in first_rows
    }
    assert first_versions == {
        updated_card["card_id"]: updated_card["current_version"][
            "card_version_id"
        ],
        deprecated_card["card_id"]: deprecated_card["current_version"][
            "card_version_id"
        ],
    }
    assert [(row["card_id"], row["card_version_id"]) for row in second_rows] == [
        (updated_card["card_id"], version_two_id)
    ]

    assert client.post(
        f"/decks/{deck['deck_id']}/cards/{updated_card['card_id']}/remove",
        json={"action": "removed"},
    ).status_code == 200
    third_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).json()
    third_export = client.get(
        f"/decks/{deck['deck_id']}/releases/"
        f"{third_release['release_id']}/export.csv"
    )
    assert third_export.status_code == 200
    assert third_export.headers["x-row-count"] == "0"
    assert list(
        csv.DictReader(io.StringIO(third_export.content.decode("utf-8")))
    ) == []


def test_release_csv_rejects_release_from_another_deck(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Release Errada")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "csv-wrong-deck"),
    )
    source_deck = create_deck(client, discipline, "Deck Fonte CSV")
    other_deck = create_deck(client, discipline, "Outro Deck CSV")
    assert client.post(
        f"/decks/{source_deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    release = client.post(
        f"/decks/{source_deck['deck_id']}/publish-release",
        json={},
    ).json()

    response = client.get(
        f"/decks/{other_deck['deck_id']}/releases/"
        f"{release['release_id']}/export.csv"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Release not found in this deck"}


def test_subscriber_can_fetch_manifest_and_initial_anki_snapshot(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Assinatura")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "subscription-initial-card"),
    )
    deck = create_deck(client, discipline, "Deck Assinavel")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Primeira release assinavel"},
    ).status_code == 201

    bearer_client = create_bearer_client(session)
    try:
        available = bearer_client.get("/subscriptions/decks")
        assert available.status_code == 200
        available_decks = {
            item["deck_id"]: item for item in available.json()["items"]
        }
        assert available_decks[deck["deck_id"]]["subscribed"] is False
        assert available_decks[deck["deck_id"]]["latest_release"] == 1

        subscription = bearer_client.post(
            f"/subscriptions/{deck['deck_id']}"
        )
        assert subscription.status_code == 200
        assert subscription.json()["deck_id"] == deck["deck_id"]
        assert subscription.json()["latest_release"] == 1
        assert subscription.json()["active_card_count"] == 1

        manifest = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/manifest"
        )
        assert manifest.status_code == 200
        assert manifest.json()["note_type"] == "Anki Concursos Basic"
        assert manifest.json()["fields"] == [
            "Front",
            "Back",
            "Answer",
            "Explanation",
        ]
        assert manifest.json()["latest_release"] == 1

        sync = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/sync?since_release=0"
        )
        assert sync.status_code == 200
        body = sync.json()
        assert body["from_release"] == 0
        assert body["to_release"] == 1
        assert body["has_changes"] is True
        assert body["changes"] == [
            {
                "release_id": body["changes"][0]["release_id"],
                "release_number": 1,
                "published_at": body["changes"][0]["published_at"],
                "action": "added",
                "card_id": card["card_id"],
                "public_id": card["public_id"],
                "old_card_version_id": None,
                "new_card_version_id": card["current_version"]["card_version_id"],
                "card_kind": "basic",
                "note_type": "Anki Concursos Basic",
                "template_name": None,
                "fields": {
                    "Front": card["current_version"]["front_text"],
                    "Back": card["current_version"]["back_text"],
                    "Answer": card["current_version"]["answer_text"],
                    "Explanation": card["current_version"]["explanation_text"],
                },
                "template": None,
                "source_note_id": None,
                "source_note_guid": None,
                "source_deck_path": None,
                "tags": [
                    f"deck::{deck['deck_id']}",
                    f"card::{card['public_id']}",
                ],
            }
        ]
    finally:
        app.dependency_overrides.clear()


def test_addon_status_exposes_version_contract() -> None:
    response = TestClient(app).get("/addon/status")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "1",
        "min_addon_version": "0.1.0",
        "supported_note_types": ["basic", "cloze"],
    }


def test_addon_sync_supports_real_pagination(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Addon Paginado")
    cards = [
        approve_and_publish(
            client,
            create_card(
                client,
                discipline,
                topic,
                f"addon-paginated-card-{index}",
            ),
        )
        for index in range(3)
    ]
    deck = create_deck(client, discipline, "Deck Addon Paginado")
    for card in cards:
        assert client.post(
            f"/decks/{deck['deck_id']}/cards",
            json={"card_id": card["card_id"]},
        ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).status_code == 201

    bearer_client = create_bearer_client(session)
    try:
        assert bearer_client.post(
            f"/subscriptions/{deck['deck_id']}"
        ).status_code == 200
        first_page = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/sync",
            params={"since_release": 0, "page": 1, "page_size": 2},
        )
        second_page = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/sync",
            params={"since_release": 0, "page": 2, "page_size": 2},
        )
    finally:
        app.dependency_overrides.clear()

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["page"] == 1
    assert first_page.json()["pages"] == 2
    assert first_page.json()["total_changes"] == 3
    assert len(first_page.json()["changes"]) == 2
    assert second_page.json()["page"] == 2
    assert second_page.json()["pages"] == 2
    assert second_page.json()["total_changes"] == 3
    assert len(second_page.json()["changes"]) == 1
    assert [
        change["public_id"]
        for change in first_page.json()["changes"] + second_page.json()["changes"]
    ] == sorted(card["public_id"] for card in cards)


def test_addon_sync_requires_active_subscription(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Sync Bloqueado")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "subscription-required-card"),
    )
    deck = create_deck(client, discipline, "Deck Sync Bloqueado")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).status_code == 201

    bearer_client = create_bearer_client(session)
    try:
        response = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/manifest"
        )
        assert response.status_code == 403
        assert response.json() == {
            "detail": "Subscribe to this deck before syncing it"
        }
    finally:
        app.dependency_overrides.clear()


def test_addon_sync_returns_cloze_note_type(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Addon Cloze")
    card = approve_and_publish(
        client,
        create_card(
            client,
            discipline,
            topic,
            "addon-cloze-card",
            card_kind="cloze",
            front_text="A Constituicao admite {{c1::habeas corpus}}.",
        ),
    )
    deck = create_deck(client, discipline, "Deck Addon Cloze")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).status_code == 201

    bearer_client = create_bearer_client(session)
    try:
        assert bearer_client.post(
            f"/subscriptions/{deck['deck_id']}"
        ).status_code == 200
        sync = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/sync?since_release=0"
        )
        assert sync.status_code == 200
        change = sync.json()["changes"][0]
        assert change["card_kind"] == "cloze"
        assert change["note_type"] == "Anki Concursos Cloze"
        assert change["fields"] == {
            "Text": "A Constituicao admite {{c1::habeas corpus}}.",
            "Extra": card["current_version"]["back_text"],
            "Answer": card["current_version"]["answer_text"],
            "Explanation": card["current_version"]["explanation_text"],
        }
    finally:
        app.dependency_overrides.clear()


def test_anki_delta_sync_returns_updated_and_removed_cards(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Delta Addon")
    updated_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "addon-updated-card"),
    )
    removed_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "addon-removed-card"),
    )
    deck = create_deck(client, discipline, "Deck Delta Addon")
    for card in (updated_card, removed_card):
        assert client.post(
            f"/decks/{deck['deck_id']}/cards",
            json={"card_id": card["card_id"]},
        ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={},
    ).status_code == 201

    bearer_client = create_bearer_client(session)
    try:
        assert bearer_client.post(
            f"/subscriptions/{deck['deck_id']}"
        ).status_code == 200

        version_two_id = create_and_publish_new_version(
            client,
            updated_card,
            "addon",
        )
        assert client.post(
            f"/decks/{deck['deck_id']}/cards",
            json={"card_id": updated_card["card_id"]},
        ).status_code == 200
        assert client.post(
            f"/decks/{deck['deck_id']}/cards/{removed_card['card_id']}/remove",
            json={"action": "removed"},
        ).status_code == 200
        assert client.post(
            f"/decks/{deck['deck_id']}/publish-release",
            json={"description": "Delta addon"},
        ).status_code == 201

        sync = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/sync?since_release=1"
        )
        assert sync.status_code == 200
        changes = {item["card_id"]: item for item in sync.json()["changes"]}
        assert changes[updated_card["card_id"]]["action"] == "updated"
        assert (
            changes[updated_card["card_id"]]["old_card_version_id"]
            == updated_card["current_version"]["card_version_id"]
        )
        assert (
            changes[updated_card["card_id"]]["new_card_version_id"]
            == version_two_id
        )
        assert changes[updated_card["card_id"]]["fields"]["Front"] == (
            "Frente revisada addon"
        )
        assert changes[removed_card["card_id"]]["action"] == "removed"
        assert (
            changes[removed_card["card_id"]]["old_card_version_id"]
            == removed_card["current_version"]["card_version_id"]
        )
        assert changes[removed_card["card_id"]]["new_card_version_id"] is None
        assert changes[removed_card["card_id"]]["fields"] is None

        initial_sync = bearer_client.get(
            f"/addon/decks/{deck['deck_id']}/sync?since_release=0"
        )
        assert initial_sync.status_code == 200
        assert [
            item["card_id"] for item in initial_sync.json()["changes"]
        ] == [updated_card["card_id"]]
        assert initial_sync.json()["changes"][0]["action"] == "added"
        assert (
            initial_sync.json()["changes"][0]["new_card_version_id"]
            == version_two_id
        )
    finally:
        app.dependency_overrides.clear()


def test_empty_deck_has_no_releases_or_sync_changes(
    session: Session, client: TestClient
) -> None:
    discipline, _topic = create_taxonomy(session, "Sync Vazio")
    deck = create_deck(client, discipline, "Deck Sync Vazio")

    releases = client.get(f"/decks/{deck['deck_id']}/releases")
    sync = client.get(f"/decks/{deck['deck_id']}/sync")

    assert releases.status_code == 200
    assert releases.json() == {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
        "pages": 0,
        "latest_release": 0,
    }
    assert sync.status_code == 200
    assert sync.json() == {
        "deck_id": deck["deck_id"],
        "from_release": 0,
        "to_release": 0,
        "has_changes": False,
        "changes": [],
    }


def test_release_list_is_paginated_and_counts_actions(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Lista Releases")
    card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "release-list-card"),
    )
    deck = create_deck(client, discipline, "Deck Lista Releases")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    first_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Release inicial"},
    ).json()

    version_two_id = create_and_publish_new_version(client, card, "lista")
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": card["card_id"]},
    ).status_code == 200
    second_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Release atualizada"},
    ).json()

    first_page = client.get(
        f"/decks/{deck['deck_id']}/releases",
        params={"page": 1, "page_size": 1},
    )
    second_page = client.get(
        f"/decks/{deck['deck_id']}/releases",
        params={"page": 2, "page_size": 1},
    )

    assert first_page.status_code == 200
    assert first_page.json() == {
        "items": [
            {
                "release_id": second_release["release_id"],
                "deck_id": deck["deck_id"],
                "release_number": 2,
                "published_at": second_release["published_at"],
                "description": "Release atualizada",
                "item_count": 1,
                "actions": {
                    "added": 0,
                    "updated": 1,
                    "removed": 0,
                    "deprecated": 0,
                },
            }
        ],
        "page": 1,
        "page_size": 1,
        "total": 2,
        "pages": 2,
        "latest_release": 2,
    }
    assert second_page.status_code == 200
    assert second_page.json()["items"][0]["release_id"] == first_release[
        "release_id"
    ]
    assert second_page.json()["items"][0]["actions"] == {
        "added": 1,
        "updated": 0,
        "removed": 0,
        "deprecated": 0,
    }
    assert version_two_id == second_release["items"][0]["card_version_id"]


def test_sync_returns_ordered_incremental_changes_with_old_and_new_versions(
    session: Session, client: TestClient
) -> None:
    discipline, topic = create_taxonomy(session, "Sync Incremental")
    updated_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "sync-updated"),
    )
    removed_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "sync-removed"),
    )
    deprecated_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "sync-deprecated"),
    )
    added_card = approve_and_publish(
        client,
        create_card(client, discipline, topic, "sync-added-later"),
    )
    deck = create_deck(client, discipline, "Deck Sync Incremental")
    for card in (updated_card, removed_card, deprecated_card):
        assert client.post(
            f"/decks/{deck['deck_id']}/cards",
            json={"card_id": card["card_id"]},
        ).status_code == 200
    first_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Base para sync"},
    ).json()

    updated_version_id = create_and_publish_new_version(
        client, updated_card, "sync"
    )
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": updated_card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards",
        json={"card_id": added_card["card_id"]},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards/{removed_card['card_id']}/remove",
        json={"action": "removed"},
    ).status_code == 200
    assert client.post(
        f"/decks/{deck['deck_id']}/cards/"
        f"{deprecated_card['card_id']}/remove",
        json={"action": "deprecated"},
    ).status_code == 200
    second_release = client.post(
        f"/decks/{deck['deck_id']}/publish-release",
        json={"description": "Delta completo"},
    ).json()

    response = client.get(
        f"/decks/{deck['deck_id']}/sync",
        params={"since_release": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deck_id"] == deck["deck_id"]
    assert payload["from_release"] == 1
    assert payload["to_release"] == 2
    assert payload["has_changes"] is True
    assert {
        change["release_id"] for change in payload["changes"]
    } == {second_release["release_id"]}
    assert {
        change["release_number"] for change in payload["changes"]
    } == {2}
    changes = {
        change["card_id"]: change for change in payload["changes"]
    }
    assert changes[updated_card["card_id"]] == {
        "release_id": second_release["release_id"],
        "release_number": 2,
        "published_at": second_release["published_at"],
        "action": "updated",
        "card_id": updated_card["card_id"],
        "public_id": updated_card["public_id"],
        "old_card_version_id": updated_card["current_version"][
            "card_version_id"
        ],
        "new_card_version_id": updated_version_id,
    }
    assert changes[added_card["card_id"]][
        "old_card_version_id"
    ] is None
    assert changes[added_card["card_id"]][
        "new_card_version_id"
    ] == added_card["current_version"]["card_version_id"]
    assert changes[removed_card["card_id"]][
        "old_card_version_id"
    ] == removed_card["current_version"]["card_version_id"]
    assert changes[removed_card["card_id"]][
        "new_card_version_id"
    ] is None
    assert changes[deprecated_card["card_id"]]["action"] == "deprecated"
    assert changes[deprecated_card["card_id"]][
        "old_card_version_id"
    ] == deprecated_card["current_version"]["card_version_id"]
    assert changes[deprecated_card["card_id"]][
        "new_card_version_id"
    ] is None

    full_sync = client.get(
        f"/decks/{deck['deck_id']}/sync",
        params={"since_release": 0},
    )
    assert full_sync.status_code == 200
    assert full_sync.json()["from_release"] == 0
    assert full_sync.json()["to_release"] == 2
    assert len(full_sync.json()["changes"]) == 7
    assert [
        change["release_number"] for change in full_sync.json()["changes"]
    ] == sorted(
        change["release_number"] for change in full_sync.json()["changes"]
    )
    assert first_release["release_id"] in {
        change["release_id"] for change in full_sync.json()["changes"]
    }

    current_sync = client.get(
        f"/decks/{deck['deck_id']}/sync",
        params={"since_release": 2},
    )
    assert current_sync.status_code == 200
    assert current_sync.json()["has_changes"] is False
    assert current_sync.json()["changes"] == []


def test_sync_rejects_unknown_release_number(
    session: Session, client: TestClient
) -> None:
    discipline, _topic = create_taxonomy(session, "Sync Invalido")
    deck = create_deck(client, discipline, "Deck Sync Invalido")

    response = client.get(
        f"/decks/{deck['deck_id']}/sync",
        params={"since_release": 1},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Release number not found in this deck"
    }


def test_deck_endpoints_require_admin_api_key() -> None:
    unauthorized = TestClient(app).get(f"/decks/{uuid.uuid4()}")
    assert unauthorized.status_code == 401


def test_deck_list_is_paginated_and_returns_summaries(
    session: Session,
    client: TestClient,
) -> None:
    discipline, _topic = create_taxonomy(session, "Lista Decks")
    create_deck(client, discipline, "Deck B")
    create_deck(client, discipline, "Deck A")

    response = client.get("/decks", params={"page": 1, "page_size": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["pages"] == 2
    assert body["items"][0]["name"] == "Deck A"
    assert body["items"][0]["active_card_count"] == 0
    assert "cards" not in body["items"][0]


def test_addon_can_upload_full_deck_package_and_publish_release(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Completo",
        "description": "Baralho completo enviado pelo addon",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Basic",
                "note_type": "Anki Concursos Basic",
                "card_kind": "basic",
                "fields": [
                    "Front",
                    "Back",
                    "Answer",
                    "Explanation",
                ],
                "field_mapping": {
                    "Front": "front_text",
                    "Back": "back_text",
                    "Answer": "answer_text",
                    "Explanation": "explanation_text",
                },
                "front_html": "<div class=\"front\">{{Front}}</div>",
                "back_html": "<div class=\"back\">{{Back}}</div>",
                "styling_css": ".card { font-family: Inter; }",
            }
        ],
        "notes": [
            {
                "note_type": "Anki Concursos Basic",
                "card_kind": "basic",
                "fields": {
                    "Front": "Qual é a capital do Brasil?",
                    "Back": "Brasília.",
                    "Answer": "Brasília.",
                    "Explanation": "Capital federal do Brasil.",
                },
                "tags": ["geografia", "capital"],
            }
        ],
    }

    response = student_client.post("/addon/decks/upload", json=upload_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["deck_name"] == "Deck Upload Completo"
    assert body["published"] is True
    assert body["total_notes"] == 1
    assert body["created_cards"] == 1
    assert body["reused_cards"] == 0
    assert body["latest_release"] == 1
    assert body["items"][0]["status"] == "created"
    assert body["items"][0]["note_type"] == "Anki Concursos Basic"
    assert body["items"][0]["card_kind"] == "basic"

    subscriber_client = create_bearer_client(session)
    try:
        assert subscriber_client.post(
            f"/subscriptions/{body['deck_id']}"
        ).status_code == 200
        manifest = subscriber_client.get(
            f"/addon/decks/{body['deck_id']}/manifest"
        )
    finally:
        app.dependency_overrides.clear()

    assert manifest.status_code == 200
    manifest_body = manifest.json()
    assert manifest_body["note_type"] == "Anki Concursos Basic"
    assert manifest_body["fields"] == [
        "Front",
        "Back",
        "Answer",
        "Explanation",
    ]
    assert manifest_body["templates"][0]["template_name"] == "Basic"
    assert manifest_body["templates"][0]["styling_css"] == ".card { font-family: Inter; }"


def test_addon_upload_reuses_cards_for_identical_content(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Dedup",
        "description": "Baralho deduplicado",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Basic",
                "note_type": "Anki Concursos Basic",
                "card_kind": "basic",
                "fields": [
                    "Front",
                    "Back",
                    "Answer",
                    "Explanation",
                ],
                "field_mapping": {
                    "Front": "front_text",
                    "Back": "back_text",
                    "Answer": "answer_text",
                    "Explanation": "explanation_text",
                },
                "front_html": "<div>{{Front}}</div>",
                "back_html": "<div>{{Back}}</div>",
                "styling_css": ".card { font-family: Inter; }",
            }
        ],
        "notes": [
            {
                "note_type": "Anki Concursos Basic",
                "card_kind": "basic",
                "fields": {
                    "Front": "Qual é a capital do Brasil?",
                    "Back": "Brasília.",
                    "Answer": "Brasília.",
                    "Explanation": "Capital federal do Brasil.",
                },
                "tags": ["geografia", "capital"],
            }
        ],
    }

    first = student_client.post("/addon/decks/upload", json=upload_payload)
    second = student_client.post("/addon/decks/upload", json=upload_payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["created_cards"] == 1
    assert second.json()["created_cards"] == 0
    assert second.json()["reused_cards"] == 1
    assert second.json()["published"] is False
    assert second.json()["latest_release"] == 1
    assert second.json()["items"][0]["status"] == "reused"


def test_addon_can_upload_multiple_note_types_in_one_deck(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Multitipo",
        "description": "Baralho com Basic e Cloze",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Getting Started Basic",
                "note_type": "Getting Started Basic",
                "card_kind": "basic",
                "fields": [
                    "Lesson",
                    "Prompt",
                    "Answer",
                    "Extra",
                    "ankihub_id",
                ],
                "field_mapping": {
                    "Lesson": "front_text",
                    "Prompt": "back_text",
                    "Answer": "answer_text",
                    "Extra": "explanation_text",
                },
                "front_html": "<div>{{Lesson}}</div>",
                "back_html": "<div>{{Prompt}}</div>",
                "styling_css": ".card { font-family: Inter; }",
            },
            {
                "template_name": "Getting Started Cloze",
                "note_type": "Getting Started Cloze",
                "card_kind": "cloze",
                "fields": [
                    "Lesson",
                    "Cloze",
                    "Extra",
                    "Deep Dive",
                    "ankihub_id",
                ],
                "field_mapping": {
                    "Cloze": "front_text",
                    "Lesson": "back_text",
                    "Extra": "answer_text",
                    "Deep Dive": "explanation_text",
                },
                "front_html": "<div>{{Cloze}}</div>",
                "back_html": "<div>{{Lesson}}</div>",
                "styling_css": ".card { font-family: Inter; }",
            },
        ],
        "notes": [
            {
                "note_type": "Getting Started Basic",
                "card_kind": "basic",
                "fields": {
                    "Lesson": "Introducao ao sistema",
                    "Prompt": "O que o sistema faz?",
                    "Answer": "Recebe e distribui baralhos",
                    "Extra": "Baralho base",
                    "ankihub_id": "basic-1",
                },
            },
            {
                "note_type": "Getting Started Cloze",
                "card_kind": "cloze",
                "fields": {
                    "Lesson": "Anki will create cards from the note above.",
                    "Cloze": "Anki will create {{c1::two::#}} cards from the note above.",
                    "Extra": "Cloze example",
                    "Deep Dive": "Cloze notes can generate multiple cards.",
                    "ankihub_id": "cloze-1",
                },
            },
        ],
    }

    response = student_client.post("/addon/decks/upload", json=upload_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["total_notes"] == 2
    assert body["created_cards"] == 2
    assert body["items"][0]["card_kind"] == "basic"
    assert body["items"][1]["card_kind"] == "cloze"


def test_addon_upload_allows_missing_explanation_field(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Sem Explicacao",
        "description": "Baralho sem explanation_text",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Basic Sem Explicacao",
                "note_type": "Basic Sem Explicacao",
                "card_kind": "basic",
                "fields": ["Front", "Back", "Answer"],
                "field_mapping": {
                    "Front": "front_text",
                    "Back": "back_text",
                    "Answer": "answer_text",
                },
                "front_html": "<div>{{Front}}</div>",
                "back_html": "<div>{{Back}}</div>",
                "styling_css": ".card { font-family: Inter; }",
            }
        ],
        "notes": [
            {
                "note_type": "Basic Sem Explicacao",
                "card_kind": "basic",
                "fields": {
                    "Front": "Pergunta de teste",
                    "Back": "Resposta de teste",
                    "Answer": "Resposta de teste",
                },
            }
        ],
    }

    response = student_client.post("/addon/decks/upload", json=upload_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["created_cards"] == 1
    assert body["items"][0]["status"] == "created"


def test_addon_upload_distinguishes_note_type_in_canonical_key(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Canonical Key",
        "description": "Baralho com conteudo igual em tipos diferentes",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Type A",
                "note_type": "Type A",
                "card_kind": "basic",
                "fields": ["Front", "Back"],
                "field_mapping": {
                    "Front": "front_text",
                    "Back": "back_text",
                },
                "front_html": "<div>{{Front}}</div>",
                "back_html": "<div>{{Back}}</div>",
                "styling_css": "",
            },
            {
                "template_name": "Type B",
                "note_type": "Type B",
                "card_kind": "basic",
                "fields": ["Front", "Back"],
                "field_mapping": {
                    "Front": "front_text",
                    "Back": "back_text",
                },
                "front_html": "<div>{{Front}}</div>",
                "back_html": "<div>{{Back}}</div>",
                "styling_css": "",
            },
        ],
        "notes": [
            {
                "note_type": "Type A",
                "template_name": "Type A",
                "card_kind": "basic",
                "fields": {
                    "Front": "Conteudo idêntico",
                    "Back": "Resposta idêntica",
                },
            },
            {
                "note_type": "Type B",
                "template_name": "Type B",
                "card_kind": "basic",
                "fields": {
                    "Front": "Conteudo idêntico",
                    "Back": "Resposta idêntica",
                },
            },
        ],
    }

    response = student_client.post("/addon/decks/upload", json=upload_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["created_cards"] == 2
    assert body["reused_cards"] == 0
    assert {item["note_type"] for item in body["items"]} == {"Type A", "Type B"}


def test_addon_upload_recovers_cloze_markup_from_any_raw_field(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Cloze Recovery",
        "description": "Baralho cloze com marcação fora do front_text",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Getting Started Cloze",
                "note_type": "Getting Started Cloze",
                "card_kind": "cloze",
                "fields": [
                    "Lesson",
                    "Cloze",
                    "Extra",
                    "Deep Dive",
                ],
                "field_mapping": {
                    "Lesson": "front_text",
                    "Cloze": "back_text",
                    "Extra": "answer_text",
                    "Deep Dive": "explanation_text",
                },
                "front_html": "<div>{{Lesson}}</div>",
                "back_html": "<div>{{Cloze}}</div>",
                "styling_css": ".card { font-family: Inter; }",
            }
        ],
        "notes": [
            {
                "note_type": "Getting Started Cloze",
                "template_name": "Getting Started Cloze",
                "card_kind": "cloze",
                "fields": {
                    "Lesson": "Anki will create cards from the note above.",
                    "Cloze": "Anki will create {{c1::two::#}} cards from the note above.",
                    "Extra": "Cloze example",
                    "Deep Dive": "Cloze notes can generate multiple cards.",
                },
            }
        ],
    }

    response = student_client.post("/addon/decks/upload", json=upload_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["created_cards"] == 1
    assert body["items"][0]["status"] == "created"
    assert body["items"][0]["card_kind"] == "cloze"


def test_addon_upload_syncs_native_anki_fields_and_template(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Anki Nativo",
        "description": "Baralho sem campos canonicos",
        "source_name": "addon",
        "source_deck_path": "Concurso::Direito",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Modelo Personalizado",
                "note_type": "Modelo Personalizado",
                "card_kind": "basic",
                "fields": ["Enunciado", "Alternativas", "Comentario"],
                "field_mapping": {},
                "front_html": "<section>{{Enunciado}}</section>",
                "back_html": "<section>{{Alternativas}}{{Comentario}}</section>",
                "styling_css": ".card { color: #111827; }",
            }
        ],
        "notes": [
            {
                "note_type": "Modelo Personalizado",
                "template_name": "Modelo Personalizado",
                "card_kind": "basic",
                "source_note_id": "1714851485108",
                "source_note_guid": "native-guid-1",
                "source_deck_path": "Concurso::Direito::Constitucional",
                "fields": {
                    "Enunciado": "Julgue o item.",
                    "Alternativas": "Certo ou errado",
                    "Comentario": "Comentário livre.",
                },
                "tags": ["constitucional", "controle"],
            }
        ],
    }

    upload = student_client.post("/addon/decks/upload", json=upload_payload)
    assert upload.status_code == 201
    upload_body = upload.json()
    assert upload_body["created_cards"] == 1
    assert upload_body["updated_cards"] == 0

    sync_client = create_bearer_client(session)
    try:
        assert sync_client.post(
            f"/subscriptions/{upload_body['deck_id']}"
        ).status_code == 200
        sync = sync_client.get(
            f"/addon/decks/{upload_body['deck_id']}/sync?since_release=0"
        )
    finally:
        app.dependency_overrides.clear()

    assert sync.status_code == 200
    change = sync.json()["changes"][0]
    assert change["note_type"] == "Modelo Personalizado"
    assert change["template_name"] == "Modelo Personalizado"
    assert change["fields"] == upload_payload["notes"][0]["fields"]
    assert change["template"]["front_html"] == "<section>{{Enunciado}}</section>"
    assert change["template"]["styling_css"] == ".card { color: #111827; }"
    assert change["source_note_id"] == "1714851485108"
    assert change["source_note_guid"] == "native-guid-1"
    assert change["source_deck_path"] == "Concurso::Direito::Constitucional"
    assert "constitucional" in change["tags"]


def test_addon_reupload_same_source_note_creates_new_card_version(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Atualizacao Anki",
        "description": "Baralho com nota atualizada",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Modelo Livre",
                "note_type": "Modelo Livre",
                "card_kind": "basic",
                "fields": ["Pergunta", "Resposta"],
                "field_mapping": {},
                "front_html": "<div>{{Pergunta}}</div>",
                "back_html": "<div>{{Resposta}}</div>",
                "styling_css": "",
            }
        ],
        "notes": [
            {
                "note_type": "Modelo Livre",
                "template_name": "Modelo Livre",
                "card_kind": "basic",
                "source_note_id": "note-1",
                "fields": {
                    "Pergunta": "Pergunta original",
                    "Resposta": "Resposta original",
                },
            }
        ],
    }

    first = student_client.post("/addon/decks/upload", json=upload_payload)
    assert first.status_code == 201
    first_body = first.json()
    first_item = first_body["items"][0]

    upload_payload["notes"][0]["fields"]["Resposta"] = "Resposta atualizada"
    second = student_client.post("/addon/decks/upload", json=upload_payload)

    assert second.status_code == 201
    second_body = second.json()
    second_item = second_body["items"][0]
    assert second_body["created_cards"] == 0
    assert second_body["updated_cards"] == 1
    assert second_item["status"] == "updated"
    assert second_item["card_id"] == first_item["card_id"]
    assert second_item["card_version_id"] != first_item["card_version_id"]
    assert second_body["latest_release"] == 2


def test_addon_upload_allows_same_source_note_with_multiple_templates(
    session: Session,
) -> None:
    student_client = create_bearer_client(session)
    upload_payload = {
        "deck_name": "Deck Upload Multi Card Note",
        "description": "Uma nota Anki gerando dois cards",
        "source_name": "addon",
        "publish_release": True,
        "templates": [
            {
                "template_name": "Forward",
                "note_type": "Vocabulario",
                "card_kind": "basic",
                "fields": ["Termo", "Definicao"],
                "field_mapping": {},
                "front_html": "<div>{{Termo}}</div>",
                "back_html": "<div>{{Definicao}}</div>",
                "styling_css": "",
            },
            {
                "template_name": "Reverse",
                "note_type": "Vocabulario",
                "card_kind": "basic",
                "fields": ["Termo", "Definicao"],
                "field_mapping": {},
                "front_html": "<div>{{Definicao}}</div>",
                "back_html": "<div>{{Termo}}</div>",
                "styling_css": "",
            },
        ],
        "notes": [
            {
                "note_type": "Vocabulario",
                "template_name": "Forward",
                "card_kind": "basic",
                "source_note_id": "same-note",
                "fields": {
                    "Termo": "Mandado de seguranca",
                    "Definicao": "Remedio constitucional",
                },
            },
            {
                "note_type": "Vocabulario",
                "template_name": "Reverse",
                "card_kind": "basic",
                "source_note_id": "same-note",
                "fields": {
                    "Termo": "Mandado de seguranca",
                    "Definicao": "Remedio constitucional",
                },
            },
        ],
    }

    response = student_client.post("/addon/decks/upload", json=upload_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["created_cards"] == 2
    assert body["reused_cards"] == 0
    assert {item["status"] for item in body["items"]} == {"created"}
    assert len({item["card_id"] for item in body["items"]}) == 2
