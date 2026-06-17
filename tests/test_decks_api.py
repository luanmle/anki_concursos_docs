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
                "fields": {
                    "Front": card["current_version"]["front_text"],
                    "Back": card["current_version"]["back_text"],
                    "Answer": card["current_version"]["answer_text"],
                    "Explanation": card["current_version"]["explanation_text"],
                },
                "tags": [
                    f"deck::{deck['deck_id']}",
                    f"card::{card['public_id']}",
                ],
            }
        ]
    finally:
        app.dependency_overrides.clear()


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
