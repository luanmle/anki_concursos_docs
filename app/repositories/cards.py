import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Card, CardVersion, Discipline, Topic
from app.models.enums import CardStatus


class CardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, card_id: uuid.UUID, *, for_update: bool = False) -> Card | None:
        statement = (
            select(Card)
            .options(
                joinedload(Card.current_version),
                selectinload(Card.versions),
            )
            .where(Card.id == card_id)
        )
        if for_update:
            statement = statement.with_for_update(of=Card)
        return self.session.scalar(statement)

    def get_by_public_id(self, public_id: str) -> Card | None:
        statement = (
            select(Card)
            .options(joinedload(Card.current_version))
            .where(
                Card.public_id == public_id.upper(),
                Card.status == CardStatus.PUBLISHED,
            )
        )
        return self.session.scalar(statement)

    def get_by_canonical_key(self, canonical_key: str) -> Card | None:
        return self.session.scalar(
            select(Card).where(Card.canonical_key == canonical_key)
        )

    def content_hash_exists(self, content_hash: str) -> bool:
        statement = select(CardVersion.id).where(
            CardVersion.content_hash == content_hash
        )
        return self.session.scalar(statement) is not None

    def get_discipline_by_name(self, name: str) -> Discipline | None:
        return self.session.scalar(
            select(Discipline).where(func.lower(Discipline.name) == name.lower())
        )

    def get_topic_by_name(self, discipline_id: uuid.UUID, name: str) -> Topic | None:
        return self.session.scalar(
            select(Topic).where(
                Topic.discipline_id == discipline_id,
                func.lower(Topic.name) == name.lower(),
            )
        )

    def get_version(
        self, card_id: uuid.UUID, version_id: uuid.UUID
    ) -> CardVersion | None:
        return self.session.scalar(
            select(CardVersion).where(
                CardVersion.id == version_id,
                CardVersion.card_id == card_id,
            )
        )

    def taxonomy_is_valid(
        self, discipline_id: uuid.UUID, topic_id: uuid.UUID
    ) -> bool:
        statement = (
            select(Topic.id)
            .join(Discipline, Discipline.id == Topic.discipline_id)
            .where(
                Discipline.id == discipline_id,
                Topic.id == topic_id,
                Topic.discipline_id == discipline_id,
            )
        )
        return self.session.scalar(statement) is not None

    def create_card(self, card: Card) -> Card:
        self.session.add(card)
        self.session.flush()
        return card

    def create_version(self, version: CardVersion) -> CardVersion:
        self.session.add(version)
        self.session.flush()
        return version

    def next_version_number(self, card_id: uuid.UUID) -> int:
        current_max = self.session.scalar(
            select(func.max(CardVersion.version_number)).where(
                CardVersion.card_id == card_id
            )
        )
        return (current_max or 0) + 1

    def list_cards(
        self,
        *,
        page: int,
        page_size: int,
        discipline_id: uuid.UUID | None,
        topic_id: uuid.UUID | None,
        status: CardStatus | None,
        public_id: str | None,
    ) -> tuple[list[Card], int]:
        filters = []
        if discipline_id is not None:
            filters.append(Card.discipline_id == discipline_id)
        if topic_id is not None:
            filters.append(Card.topic_id == topic_id)
        if status is not None:
            filters.append(Card.status == status)
        if public_id is not None:
            filters.append(Card.public_id == public_id.upper())

        total = self.session.scalar(
            select(func.count()).select_from(Card).where(*filters)
        ) or 0
        statement = (
            select(Card)
            .options(joinedload(Card.current_version))
            .where(*filters)
            .order_by(Card.created_at.desc(), Card.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total
