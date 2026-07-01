from datetime import UTC, datetime
from hashlib import sha256
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Base,
    Card,
    CardReport,
    CardVersion,
    Deck,
    DeckCard,
    Discipline,
    ProcessingJob,
    RawDocument,
    Release,
    ReleaseItem,
    ReviewTask,
    Topic,
)
from app.models.enums import (
    CardReportStatus,
    CardVersionStatus,
    ProcessingJobStatus,
    ReportType,
    ReleaseAction,
    ReviewDecision,
    ReviewTaskStatus,
)


def test_mvp_1_tables_are_declared() -> None:
    assert set(Base.metadata.tables) == {
        "raw_documents", "exams", "questions", "question_alternatives",
        "disciplines", "topics", "cards", "card_versions", "decks",
        "deck_cards", "deck_subscriptions", "deck_snapshots",
        "deck_templates", "deck_template_versions",
        "releases", "release_items",
        "processing_jobs",
        "card_reports", "note_suggestions", "suggestion_comments", "note_comments",
        "review_tasks", "users",
    }


def test_foreign_keys_reject_unknown_taxonomy(session: Session) -> None:
    session.add(Card(
        canonical_key="invalid-taxonomy",
        discipline_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        topic_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
    ))
    with pytest.raises(IntegrityError):
        session.commit()


def test_card_gets_stable_public_id(session: Session) -> None:
    discipline = Discipline(name="Direito Penal")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Teoria do crime")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="crime-concept",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.commit()

    assert card.public_id.startswith("AC-")
    assert len(card.public_id) == 35
    assert card.public_id[3:].isalnum()
    assert card.public_id == card.public_id.upper()


def test_card_public_id_is_unique(session: Session) -> None:
    discipline = Discipline(name="Direito Processual Penal")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Inquerito policial")
    session.add(topic)
    session.flush()
    public_id = "AC-0123456789ABCDEF0123456789ABCDEF"
    session.add_all(
        [
            Card(
                public_id=public_id,
                canonical_key="police-inquiry-one",
                discipline_id=discipline.id,
                topic_id=topic.id,
            ),
            Card(
                public_id=public_id,
                canonical_key="police-inquiry-two",
                discipline_id=discipline.id,
                topic_id=topic.id,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_card_public_id_is_immutable(session: Session) -> None:
    discipline = Discipline(name="Direito Empresarial")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Sociedades")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="business-company",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.commit()

    card.public_id = "AC-FEDCBA9876543210FEDCBA9876543210"
    with pytest.raises(ValueError, match="immutable"):
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
    assert card.public_id.startswith("AC-")


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


def test_card_version_can_transition_to_published(session: Session) -> None:
    discipline = Discipline(name="Direito Civil")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Obrigacoes")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="civil-obligations",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="O que e obrigacao?",
        back_text="Relacao juridica entre credor e devedor.",
        answer_text="Uma relacao juridica obrigacional.",
        explanation_text="Ela vincula prestacao e responsabilidade.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.APPROVED,
        content_hash=sha256(b"civil-obligations-v1").hexdigest(),
    )
    session.add(version)
    session.commit()

    version.status = CardVersionStatus.PUBLISHED
    session.commit()

    assert version.status == CardVersionStatus.PUBLISHED


def test_processing_job_defaults_and_entity_index(session: Session) -> None:
    entity_id = uuid.uuid4()
    job = ProcessingJob(
        job_type="extract_text",
        entity_type="raw_document",
        entity_id=entity_id,
    )
    session.add(job)
    session.commit()

    assert job.status == ProcessingJobStatus.PENDING
    assert job.input_snapshot == {}
    assert job.output_snapshot == {}
    assert {
        index.name for index in ProcessingJob.__table__.indexes
    } >= {
        "ix_processing_jobs_entity",
        "ix_processing_jobs_status_created",
    }


def test_processing_job_finish_requires_start(session: Session) -> None:
    session.add(
        ProcessingJob(
            job_type="extract_text",
            entity_type="raw_document",
            entity_id=uuid.uuid4(),
            finished_at=datetime.now(UTC),
        )
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_card_current_version_must_belong_to_same_card(session: Session) -> None:
    discipline = Discipline(name="Raciocinio Logico")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Logica proposicional")
    session.add(topic)
    session.flush()
    first_card = Card(
        canonical_key="first-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    second_card = Card(
        canonical_key="second-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add_all([first_card, second_card])
    session.flush()
    second_version = CardVersion(
        card_id=second_card.id,
        version_number=1,
        front_text="Frente",
        back_text="Verso",
        answer_text="Resposta",
        explanation_text="Explicacao",
        change_reason="Versao inicial",
        created_by="test",
        content_hash=sha256(b"second-card-v1").hexdigest(),
    )
    session.add(second_version)
    session.flush()

    first_card.current_version_id = second_version.id
    with pytest.raises(ValueError, match="same card"):
        session.commit()


def test_release_item_version_must_belong_to_same_card(session: Session) -> None:
    discipline = Discipline(name="Direito Tributario")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Obrigacao tributaria")
    session.add(topic)
    session.flush()
    first_card = Card(
        canonical_key="tax-obligation-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    second_card = Card(
        canonical_key="tax-credit-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    deck = Deck(name="Deck de Direito Tributario", discipline_id=discipline.id)
    session.add_all([first_card, second_card, deck])
    session.flush()
    second_version = CardVersion(
        card_id=second_card.id,
        version_number=1,
        front_text="Frente",
        back_text="Verso",
        answer_text="Resposta",
        explanation_text="Explicacao",
        change_reason="Versao inicial",
        created_by="test",
        content_hash=sha256(b"tax-credit-card-v1").hexdigest(),
    )
    session.add(second_version)
    session.flush()
    release = Release(deck_id=deck.id, release_number=1)
    session.add(release)
    session.flush()
    session.add(
        ReleaseItem(
            release_id=release.id,
            card_id=first_card.id,
            card_version_id=second_version.id,
            action=ReleaseAction.ADDED,
        )
    )

    with pytest.raises(ValueError, match="same card"):
        session.commit()


def test_deck_card_version_must_belong_to_same_card(session: Session) -> None:
    discipline = Discipline(name="Informatica")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Redes")
    session.add(topic)
    session.flush()
    first_card = Card(
        canonical_key="network-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    second_card = Card(
        canonical_key="security-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    deck = Deck(name="Deck de Informatica", discipline_id=discipline.id)
    session.add_all([first_card, second_card, deck])
    session.flush()
    second_version = CardVersion(
        card_id=second_card.id,
        version_number=1,
        front_text="Frente",
        back_text="Verso",
        answer_text="Resposta",
        explanation_text="Explicacao",
        change_reason="Versao inicial",
        created_by="test",
        content_hash=sha256(b"security-card-v1").hexdigest(),
    )
    session.add(second_version)
    session.flush()
    session.add(
        DeckCard(
            deck_id=deck.id,
            card_id=first_card.id,
            card_version_id=second_version.id,
        )
    )

    with pytest.raises(ValueError, match="same card"):
        session.commit()


def test_published_release_is_immutable(session: Session) -> None:
    discipline = Discipline(name="Direito Financeiro")
    session.add(discipline)
    session.flush()
    deck = Deck(name="Deck Financeiro", discipline_id=discipline.id)
    session.add(deck)
    session.flush()
    release = Release(deck_id=deck.id, release_number=1, description="Inicial")
    session.add(release)
    session.commit()

    release.description = "Alterada"
    with pytest.raises(ValueError, match="immutable"):
        session.commit()


def test_published_release_item_is_immutable(session: Session) -> None:
    discipline = Discipline(name="Direito Ambiental")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Licenciamento")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="environmental-license",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    deck = Deck(name="Deck Ambiental", discipline_id=discipline.id)
    session.add_all([card, deck])
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="O que e licenciamento ambiental?",
        back_text="Procedimento administrativo ambiental.",
        answer_text="Procedimento administrativo.",
        explanation_text="Avalia atividades potencialmente poluidoras.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"environmental-license-v1").hexdigest(),
    )
    session.add(version)
    session.flush()
    release = Release(deck_id=deck.id, release_number=1)
    session.add(release)
    session.flush()
    item = ReleaseItem(
        release_id=release.id,
        card_id=card.id,
        card_version_id=version.id,
        action=ReleaseAction.ADDED,
    )
    session.add(item)
    session.commit()

    item.action = ReleaseAction.UPDATED
    with pytest.raises(ValueError, match="immutable"):
        session.commit()


def test_card_report_version_must_belong_to_same_card(
    session: Session,
) -> None:
    discipline = Discipline(name="Direito do Trabalho")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Contrato de trabalho")
    session.add(topic)
    session.flush()
    first_card = Card(
        canonical_key="labor-card-one",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    second_card = Card(
        canonical_key="labor-card-two",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add_all([first_card, second_card])
    session.flush()
    second_version = CardVersion(
        card_id=second_card.id,
        version_number=1,
        front_text="Frente",
        back_text="Verso",
        answer_text="Resposta",
        explanation_text="Explicacao",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"labor-card-two-v1").hexdigest(),
    )
    session.add(second_version)
    session.flush()
    session.add(
        CardReport(
            card_id=first_card.id,
            card_version_id=second_version.id,
            report_type=ReportType.WRONG_ANSWER,
            message="Resposta incorreta",
        )
    )

    with pytest.raises(ValueError, match="same card"):
        session.commit()


def test_completed_review_task_is_immutable(session: Session) -> None:
    discipline = Discipline(name="Direito Internacional")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Tratados")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="international-treaty",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="O que e tratado?",
        back_text="Acordo internacional.",
        answer_text="Acordo entre sujeitos internacionais.",
        explanation_text="E regido pelo direito internacional.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"international-treaty-v1").hexdigest(),
    )
    session.add(version)
    session.flush()
    report = CardReport(
        card_id=card.id,
        card_version_id=version.id,
        report_type=ReportType.SUGGESTION,
        message="Sugestao analisada",
        status=CardReportStatus.REJECTED,
    )
    session.add(report)
    session.flush()
    task = ReviewTask(
        report_id=report.id,
        status=ReviewTaskStatus.COMPLETED,
        assigned_to="admin",
        decision=ReviewDecision.REJECTED,
        admin_comment="Nao altera o conteudo",
        reviewed_at=datetime.now(UTC),
    )
    session.add(task)
    session.commit()

    task.admin_comment = "Comentario alterado"
    with pytest.raises(ValueError, match="immutable"):
        session.commit()


def test_review_result_version_must_belong_to_reported_card(
    session: Session,
) -> None:
    discipline = Discipline(name="Direito Economico")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Ordem economica")
    session.add(topic)
    session.flush()
    reported_card = Card(
        canonical_key="reported-economic-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    other_card = Card(
        canonical_key="other-economic-card",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add_all([reported_card, other_card])
    session.flush()
    reported_version = CardVersion(
        card_id=reported_card.id,
        version_number=1,
        front_text="Frente reportada",
        back_text="Verso reportado",
        answer_text="Resposta reportada",
        explanation_text="Explicacao reportada",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"reported-economic-v1").hexdigest(),
    )
    other_version = CardVersion(
        card_id=other_card.id,
        version_number=1,
        front_text="Outra frente",
        back_text="Outro verso",
        answer_text="Outra resposta",
        explanation_text="Outra explicacao",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.NEEDS_REVIEW,
        content_hash=sha256(b"other-economic-v1").hexdigest(),
    )
    session.add_all([reported_version, other_version])
    session.flush()
    report = CardReport(
        card_id=reported_card.id,
        card_version_id=reported_version.id,
        report_type=ReportType.SUGGESTION,
        message="Criar uma versao revisada",
        status=CardReportStatus.RESOLVED,
    )
    session.add(report)
    session.flush()
    session.add(
        ReviewTask(
            report_id=report.id,
            status=ReviewTaskStatus.COMPLETED,
            assigned_to="admin",
            decision=ReviewDecision.CONVERTED_TO_NEW_VERSION,
            admin_comment="Conversao aprovada",
            resulting_card_version_id=other_version.id,
            reviewed_at=datetime.now(UTC),
        )
    )

    with pytest.raises(ValueError, match="same card"):
        session.commit()


def test_card_report_content_is_immutable(session: Session) -> None:
    discipline = Discipline(name="Direito Urbanistico")
    session.add(discipline)
    session.flush()
    topic = Topic(discipline_id=discipline.id, name="Plano diretor")
    session.add(topic)
    session.flush()
    card = Card(
        canonical_key="urban-master-plan",
        discipline_id=discipline.id,
        topic_id=topic.id,
    )
    session.add(card)
    session.flush()
    version = CardVersion(
        card_id=card.id,
        version_number=1,
        front_text="O que e plano diretor?",
        back_text="Instrumento da politica urbana.",
        answer_text="Instrumento basico da politica urbana.",
        explanation_text="Orienta o desenvolvimento municipal.",
        change_reason="Versao inicial",
        created_by="test",
        status=CardVersionStatus.PUBLISHED,
        content_hash=sha256(b"urban-master-plan-v1").hexdigest(),
    )
    session.add(version)
    session.flush()
    report = CardReport(
        card_id=card.id,
        card_version_id=version.id,
        report_type=ReportType.TYPO,
        message="Texto original do report",
    )
    session.add(report)
    session.commit()

    report.message = "Texto alterado"
    with pytest.raises(ValueError, match="immutable"):
        session.commit()
