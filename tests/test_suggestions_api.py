from hashlib import sha256
import uuid

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Card, CardVersion, Deck, DeckCard, Discipline, Topic, User
from app.models.enums import (
    CardStatus,
    CardVersionStatus,
    DeckStatus,
    NoteSuggestionStatus,
    NoteSuggestionType,
    UserRole,
)
from app.repositories import NoteSuggestionRepository
from app.schemas import (
    NoteSuggestionCommentCreateRequest,
    NoteSuggestionCreateRequest,
    NoteSuggestionReviewRequest,
)
from app.services import NoteSuggestionService


def create_user(session: Session) -> User:
    user = User(
        email=f"suggestion-{uuid.uuid4().hex}@example.com",
        display_name="Suggestion User",
        password_hash=hash_password("suggestion-password"),
        role=UserRole.STUDENT,
    )
    session.add(user)
    session.commit()
    return user


def create_published_card(session: Session) -> tuple[Card, CardVersion]:
    discipline = Discipline(name=f"Disciplina Sugestao {uuid.uuid4().hex}")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Assunto Sugestao")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key=f"suggestion-card-{uuid.uuid4()}",
        discipline_id=discipline.id,
        topic_id=topic.id,
        status=CardStatus.PUBLISHED,
    )
    session.add(card)
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="Frente original",
        back_text="Verso original",
        answer_text="Resposta original",
        explanation_text="Explicacao original",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(f"suggestion-{card.id}".encode()).hexdigest(),
    )
    session.add(version)
    session.flush()
    card.current_version_id = version.id
    session.commit()
    return card, version


def create_published_deck(session: Session) -> Deck:
    deck = Deck(
        name=f"Deck Sugestao {uuid.uuid4().hex}",
        status=DeckStatus.PUBLISHED,
    )
    session.add(deck)
    session.commit()
    return deck


def service(session: Session) -> NoteSuggestionService:
    return NoteSuggestionService(NoteSuggestionRepository(session))


def test_user_can_create_note_change_suggestion(session: Session) -> None:
    user = create_user(session)
    card, version = create_published_card(session)

    created = service(session).create_for_card(
        card.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.UPDATED_CONTENT,
            fields={"Front": "Frente sugerida"},
            added_tags=["lei", "lei", "  atualizacao  "],
            removed_tags=["antiga"],
            comment="Ajuste encontrado durante revisao.",
            source="Anki",
        ),
        user,
    )

    assert created.card_id == card.id
    assert created.public_id == card.public_id
    assert created.card_version_id == version.id
    assert created.version_number == 1
    assert created.status == NoteSuggestionStatus.PENDING
    assert created.fields == {"Front": "Frente sugerida"}
    assert created.added_tags == ["lei", "atualizacao"]

    listed = service(session).list(
        page=1,
        page_size=20,
        status_filter=NoteSuggestionStatus.PENDING,
    )
    assert listed.total == 1
    assert listed.items[0].suggestion_id == created.suggestion_id


def test_user_can_create_new_note_suggestion(session: Session) -> None:
    user = create_user(session)
    deck = create_published_deck(session)

    created = service(session).create_for_deck(
        deck.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.NEW_CARD_TO_ADD,
            fields={"Front": "Nova pergunta", "Back": "Nova resposta"},
            comment="Nova nota sugerida pelo add-on.",
        ),
        user,
    )

    assert created.deck_id == deck.id
    assert created.card_id is None
    assert created.card_version_id is None
    assert created.fields["Front"] == "Nova pergunta"


def test_reviewer_can_review_note_suggestion(session: Session) -> None:
    user = create_user(session)
    card, _version = create_published_card(session)
    created = service(session).create_for_card(
        card.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.CONTENT_ERROR,
            fields={"Back": "Verso corrigido"},
            comment="Erro de conteudo.",
        ),
        user,
    )

    reviewed = service(session).review(
        created.suggestion_id,
        NoteSuggestionReviewRequest(
            status=NoteSuggestionStatus.REJECTED,
            review_comment="Nao procede.",
        ),
        reviewed_by="reviewer@example.com",
    )

    assert reviewed.status == NoteSuggestionStatus.REJECTED
    assert reviewed.reviewed_by == "reviewer@example.com"
    assert reviewed.review_comment == "Nao procede."

    with pytest.raises(HTTPException) as exc_info:
        service(session).review(
            created.suggestion_id,
            NoteSuggestionReviewRequest(status=NoteSuggestionStatus.ACCEPTED),
            reviewed_by="reviewer@example.com",
        )
    assert exc_info.value.status_code == 409


def add_card_to_deck(session: Session, deck: Deck, card: Card, version: CardVersion) -> None:
    session.add(
        DeckCard(deck_id=deck.id, card_id=card.id, card_version_id=version.id)
    )
    session.commit()


def test_list_for_deck_includes_deck_and_card_suggestions(session: Session) -> None:
    user = create_user(session)
    deck = create_published_deck(session)
    card, version = create_published_card(session)
    add_card_to_deck(session, deck, card, version)

    # sugestao em card do deck
    card_sug = service(session).create_for_card(
        card.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.UPDATED_CONTENT,
            fields={"Front": {"old": "a", "new": "b"}},
            comment="edit card",
        ),
        user,
    )
    # sugestao de nota nova no deck
    deck_sug = service(session).create_for_deck(
        deck.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.NEW_CARD_TO_ADD,
            fields={"Front": "nova"},
            comment="new note",
        ),
        user,
    )
    # ruido: sugestao em outro deck, nao deve aparecer
    other_deck = create_published_deck(session)
    service(session).create_for_deck(
        other_deck.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.NEW_CARD_TO_ADD,
            fields={"Front": "outra"},
            comment="other deck",
        ),
        user,
    )

    listed = service(session).list_for_deck(
        deck.id, page=1, page_size=20, status_filter=None
    )
    ids = {item.suggestion_id for item in listed.items}
    assert listed.total == 2
    assert card_sug.suggestion_id in ids
    assert deck_sug.suggestion_id in ids


def test_add_and_list_comments(session: Session) -> None:
    user = create_user(session)
    card, _version = create_published_card(session)
    sug = service(session).create_for_card(
        card.id,
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.CONTENT_ERROR,
            fields={"Back": {"old": "x", "new": "y"}},
            comment="fix",
        ),
        user,
    )

    created = service(session).add_comment(
        sug.suggestion_id,
        NoteSuggestionCommentCreateRequest(body="Concordo com a mudanca."),
        user,
    )
    assert created.body == "Concordo com a mudanca."
    assert created.author_email == user.email

    listed = service(session).list_comments(sug.suggestion_id)
    assert listed.total == 1
    assert listed.items[0].comment_id == created.comment_id


def test_comment_on_missing_suggestion_raises(session: Session) -> None:
    user = create_user(session)
    with pytest.raises(HTTPException) as exc:
        service(session).add_comment(
            uuid.uuid4(),
            NoteSuggestionCommentCreateRequest(body="vazio"),
            user,
        )
    assert exc.value.status_code == 404


def test_suggestion_requires_diff_for_non_delete() -> None:
    with pytest.raises(ValidationError):
        NoteSuggestionCreateRequest(
            suggestion_type=NoteSuggestionType.UPDATED_CONTENT,
            comment="Sem alteracao.",
        )
