import csv
import hashlib
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Discipline, Topic


def create_taxonomy(session: Session, suffix: str) -> tuple[Discipline, Topic]:
    discipline = Discipline(name=f"Disciplina Deck {suffix}")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name=f"Assunto Deck {suffix}")
    session.add(topic)
    session.commit()
    return discipline, topic


def create_card(
    client: TestClient,
    discipline: Discipline,
    topic: Topic,
    canonical_key: str,
) -> dict:
    response = client.post(
        "/cards",
        json={
            "canonical_key": canonical_key,
            "discipline_id": str(discipline.id),
            "topic_id": str(topic.id),
            "front_text": f"Frente {canonical_key}",
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
