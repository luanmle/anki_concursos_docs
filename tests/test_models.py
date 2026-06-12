from hashlib import sha256
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Card, CardVersion, Discipline, RawDocument, Topic
from app.models.enums import CardVersionStatus


def test_mvp_1_tables_are_declared() -> None:
    assert set(Base.metadata.tables) == {
        "raw_documents", "exams", "questions", "question_alternatives",
        "disciplines", "topics", "cards", "card_versions", "decks",
        "deck_cards", "releases", "release_items",
    }


def test_foreign_keys_reject_unknown_taxonomy(session: Session) -> None:
    session.add(Card(
        canonical_key="invalid-taxonomy",
        discipline_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        topic_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
    ))
    with pytest.raises(IntegrityError):
        session.commit()


def test_card_version_number_is_unique_per_card(session: Session) -> None:
    discipline = Discipline(name="Direito Constitucional")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Direitos fundamentais")
    session.add(topic)
    session.flush()
    card = Card(canonical_key="habeas-corpus", discipline_id=discipline.id, topic_id=topic.id)
    session.add(card)
    session.flush()
    content = {
        "card_id": card.id,
        "version_number": 1,
        "front_text": "Qual remedio protege a liberdade de locomocao?",
        "back_text": "Habeas corpus.",
        "answer_text": "Habeas corpus.",
        "explanation_text": "Protege a liberdade de locomocao.",
        "change_reason": "Versao inicial",
        "created_by": "test",
        "status": CardVersionStatus.GENERATED,
        "content_hash": sha256(b"v1").hexdigest(),
    }
    session.add_all([CardVersion(**content), CardVersion(**content)])
    with pytest.raises(IntegrityError):
        session.commit()


def test_raw_document_hash_is_unique(session: Session) -> None:
    data = {
        "file_name": "prova.pdf",
        "file_path": "documents/prova.pdf",
        "source_type": "exam",
        "original_file_hash": sha256(b"same file").hexdigest(),
    }
    session.add_all([RawDocument(**data), RawDocument(**data)])
    with pytest.raises(IntegrityError):
        session.commit()


def test_new_version_preserves_published_version(session: Session) -> None:
    discipline = Discipline(name="Direito Administrativo")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Atos administrativos")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="atributos-ato-administrativo",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.flush()
    version_1 = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="Quais sao os atributos do ato administrativo?",
        back_text="Presuncao, imperatividade, tipicidade e autoexecutoriedade.",
        answer_text="PATI.",
        explanation_text="Sao os atributos tradicionalmente cobrados.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"published-v1").hexdigest(),
    )
    session.add(version_1)
    session.flush()
    card.current_version_id = version_1.id
    session.commit()

    version_2 = CardVersion(
        card_id=card.id,
        version_number=2,
        front_text="Quais sao os principais atributos do ato administrativo?",
        back_text="Presuncao, imperatividade, tipicidade e autoexecutoriedade.",
        answer_text="PATI.",
        explanation_text="A lista pode variar conforme a doutrina adotada.",
        change_reason="Melhoria de precisao",
        created_by="test",
        status=CardVersionStatus.APPROVED,
        content_hash=sha256(b"approved-v2").hexdigest(),
    )
    session.add(version_2)
    session.flush()
    card.current_version_id = version_2.id
    session.commit()

    session.refresh(version_1)
    assert version_1.front_text == "Quais sao os atributos do ato administrativo?"
    assert card.id == version_2.card_id
    assert card.current_version_id == version_2.id


def test_published_version_cannot_be_edited(session: Session) -> None:
    discipline = Discipline(name="Lingua Portuguesa")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Sintaxe")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="sujeito",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="O que e sujeito?",
        back_text="Termo sobre o qual se declara algo.",
        answer_text="Termo da oracao.",
        explanation_text="Relaciona-se ao predicado.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"syntax-v1").hexdigest(),
    )
    session.add(version)
    session.commit()

    version.front_text = "Texto alterado"
    with pytest.raises(ValueError, match="immutable"):
        session.commit()
