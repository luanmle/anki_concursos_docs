import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    Card,
    Deck,
    DeckCard,
    Discipline,
    Release,
    ReleaseItem,
)


class DeckRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def discipline_exists(self, discipline_id: uuid.UUID) -> bool:
        return self.session.get(Discipline, discipline_id) is not None

    def get_by_name(self, name: str) -> Deck | None:
        return self.session.scalar(select(Deck).where(Deck.name == name))

    def deck_exists(self, deck_id: uuid.UUID) -> bool:
        return (
            self.session.scalar(select(Deck.id).where(Deck.id == deck_id))
            is not None
        )

    def create(self, deck: Deck) -> Deck:
        self.session.add(deck)
        self.session.flush()
        return deck

    def get_by_id(self, deck_id: uuid.UUID, *, for_update: bool = False) -> Deck | None:
        statement = (
            select(Deck)
            .options(
                selectinload(Deck.cards).joinedload(DeckCard.card),
                selectinload(Deck.cards).joinedload(DeckCard.card_version),
            )
            .where(Deck.id == deck_id)
        )
        if for_update:
            statement = statement.with_for_update(of=Deck)
        return self.session.scalar(statement)

    def list_all(self) -> list[Deck]:
        statement = (
            select(Deck)
            .options(
                selectinload(Deck.cards).joinedload(DeckCard.card),
                selectinload(Deck.cards).joinedload(DeckCard.card_version),
            )
            .order_by(Deck.name, Deck.id)
        )
        return list(self.session.scalars(statement))

    def get_card(self, card_id: uuid.UUID) -> Card | None:
        return self.session.scalar(
            select(Card)
            .options(joinedload(Card.current_version))
            .where(Card.id == card_id)
        )

    def get_membership(self, deck_id: uuid.UUID, card_id: uuid.UUID) -> DeckCard | None:
        return self.session.scalar(
            select(DeckCard).where(
                DeckCard.deck_id == deck_id,
                DeckCard.card_id == card_id,
            )
        )

    def add_membership(self, membership: DeckCard) -> DeckCard:
        self.session.add(membership)
        self.session.flush()
        return membership

    def next_release_number(self, deck_id: uuid.UUID) -> int:
        return self.latest_release_number(deck_id) + 1

    def latest_release_number(self, deck_id: uuid.UUID) -> int:
        current_max = self.session.scalar(
            select(func.max(Release.release_number)).where(
                Release.deck_id == deck_id
            )
        )
        return current_max or 0

    def release_number_exists(
        self, deck_id: uuid.UUID, release_number: int
    ) -> bool:
        return (
            self.session.scalar(
                select(Release.id).where(
                    Release.deck_id == deck_id,
                    Release.release_number == release_number,
                )
            )
            is not None
        )

    def list_releases(
        self,
        deck_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Release], int]:
        total = self.session.scalar(
            select(func.count())
            .select_from(Release)
            .where(Release.deck_id == deck_id)
        ) or 0
        statement = (
            select(Release)
            .options(selectinload(Release.items))
            .where(Release.deck_id == deck_id)
            .order_by(Release.release_number.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def release_items(self, deck_id: uuid.UUID) -> list[ReleaseItem]:
        statement = (
            select(ReleaseItem)
            .join(Release, Release.id == ReleaseItem.release_id)
            .options(
                joinedload(ReleaseItem.card),
                joinedload(ReleaseItem.release),
            )
            .where(Release.deck_id == deck_id)
            .order_by(Release.release_number, ReleaseItem.created_at, ReleaseItem.id)
        )
        return list(self.session.scalars(statement))

    def release_items_through(
        self, deck_id: uuid.UUID, release_number: int
    ) -> list[ReleaseItem]:
        statement = (
            select(ReleaseItem)
            .join(Release, Release.id == ReleaseItem.release_id)
            .options(
                joinedload(ReleaseItem.card),
                joinedload(ReleaseItem.card_version),
                joinedload(ReleaseItem.release),
            )
            .where(
                Release.deck_id == deck_id,
                Release.release_number <= release_number,
            )
            .order_by(
                Release.release_number,
                ReleaseItem.created_at,
                ReleaseItem.id,
            )
        )
        return list(self.session.scalars(statement))

    def create_release(self, release: Release) -> Release:
        self.session.add(release)
        self.session.flush()
        return release

    def create_release_items(self, items: list[ReleaseItem]) -> None:
        self.session.add_all(items)
        self.session.flush()

    def get_release(self, release_id: uuid.UUID) -> Release | None:
        return self.session.scalar(
            select(Release)
            .options(
                joinedload(Release.deck),
                selectinload(Release.items).joinedload(ReleaseItem.card),
            )
            .where(Release.id == release_id)
        )
