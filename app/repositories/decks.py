import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    Card,
    Deck,
    DeckCard,
    DeckSnapshot,
    DeckTemplate,
    DeckTemplateVersion,
    DeckSubscription,
    Discipline,
    Release,
    ReleaseItem,
    Topic,
)
from app.models.enums import DeckStatus


class DeckRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def discipline_exists(self, discipline_id: uuid.UUID) -> bool:
        return self.session.get(Discipline, discipline_id) is not None

    def topic_exists(self, topic_id: uuid.UUID) -> bool:
        return self.session.get(Topic, topic_id) is not None

    def get_by_name(self, name: str) -> Deck | None:
        return self.session.scalar(select(Deck).where(Deck.name == name))

    def deck_exists(self, deck_id: uuid.UUID) -> bool:
        return (
            self.session.scalar(select(Deck.id).where(Deck.id == deck_id))
            is not None
        )

    def published_deck_exists(self, deck_id: uuid.UUID) -> bool:
        return (
            self.session.scalar(
                select(Deck.id).where(
                    Deck.id == deck_id,
                    Deck.status == DeckStatus.PUBLISHED,
                )
            )
            is not None
        )

    def create(self, deck: Deck) -> Deck:
        self.session.add(deck)
        self.session.flush()
        return deck

    def create_snapshot(self, snapshot: DeckSnapshot) -> DeckSnapshot:
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def list_templates(self, deck_id: uuid.UUID) -> list[DeckTemplate]:
        statement = (
            select(DeckTemplate)
            .options(
                selectinload(DeckTemplate.current_version),
                selectinload(DeckTemplate.versions),
            )
            .where(DeckTemplate.deck_id == deck_id)
            .order_by(DeckTemplate.template_name, DeckTemplate.id)
        )
        return list(self.session.scalars(statement).all())

    def get_template_by_key(self, deck_id: uuid.UUID, template_key: str) -> DeckTemplate | None:
        return self.session.scalar(
            select(DeckTemplate).where(
                DeckTemplate.deck_id == deck_id,
                DeckTemplate.template_key == template_key,
            )
        )

    def next_template_version_number(self, deck_template_id: uuid.UUID) -> int:
        next_version = self.session.scalar(
            select(func.coalesce(func.max(DeckTemplateVersion.version_number), 0) + 1).where(
                DeckTemplateVersion.deck_template_id == deck_template_id
            )
        )
        return int(next_version or 1)

    def create_template(self, template: DeckTemplate) -> DeckTemplate:
        self.session.add(template)
        self.session.flush()
        return template

    def create_template_version(self, version: DeckTemplateVersion) -> DeckTemplateVersion:
        self.session.add(version)
        self.session.flush()
        return version

    def list_template_versions(self, deck_id: uuid.UUID) -> list[DeckTemplateVersion]:
        statement = (
            select(DeckTemplateVersion)
            .join(DeckTemplate, DeckTemplateVersion.deck_template_id == DeckTemplate.id)
            .where(DeckTemplate.deck_id == deck_id)
            .order_by(DeckTemplateVersion.version_number, DeckTemplateVersion.id)
        )
        return list(self.session.scalars(statement).all())

    def get_by_id(self, deck_id: uuid.UUID, *, for_update: bool = False) -> Deck | None:
        statement = (
            select(Deck)
            .options(
                selectinload(Deck.cards).joinedload(DeckCard.card),
                selectinload(Deck.cards).joinedload(DeckCard.card_version),
                selectinload(Deck.snapshots),
            )
            .where(Deck.id == deck_id)
        )
        if for_update:
            statement = statement.with_for_update(of=Deck)
        return self.session.scalar(statement)

    def latest_snapshot(self, deck_id: uuid.UUID) -> DeckSnapshot | None:
        statement = (
            select(DeckSnapshot)
            .where(DeckSnapshot.deck_id == deck_id)
            .order_by(DeckSnapshot.created_at.desc(), DeckSnapshot.id.desc())
        )
        return self.session.scalar(statement)

    def list_decks(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Deck, int]], int]:
        total = self.session.scalar(select(func.count()).select_from(Deck)) or 0
        active_card_count = (
            select(func.count(DeckCard.id))
            .where(
                DeckCard.deck_id == Deck.id,
                DeckCard.removed_at.is_(None),
            )
            .correlate(Deck)
            .scalar_subquery()
        )
        statement = (
            select(Deck, active_card_count)
            .order_by(Deck.name, Deck.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [
            (deck, int(card_count))
            for deck, card_count in self.session.execute(statement)
        ], total

    def list_published_decks(
        self,
        *,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Deck, int, int, bool]], int]:
        total = self.session.scalar(
            select(func.count())
            .select_from(Deck)
            .where(Deck.status == DeckStatus.PUBLISHED)
        ) or 0
        active_card_count = (
            select(func.count(DeckCard.id))
            .where(
                DeckCard.deck_id == Deck.id,
                DeckCard.removed_at.is_(None),
            )
            .correlate(Deck)
            .scalar_subquery()
        )
        latest_release = (
            select(func.max(Release.release_number))
            .where(Release.deck_id == Deck.id)
            .correlate(Deck)
            .scalar_subquery()
        )
        subscribed = (
            select(func.count(DeckSubscription.id))
            .where(
                DeckSubscription.deck_id == Deck.id,
                DeckSubscription.user_id == user_id,
                DeckSubscription.unsubscribed_at.is_(None),
            )
            .correlate(Deck)
            .scalar_subquery()
        )
        statement = (
            select(Deck, active_card_count, latest_release, subscribed)
            .where(Deck.status == DeckStatus.PUBLISHED)
            .order_by(Deck.name, Deck.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [
            (
                deck,
                int(card_count),
                int(release_number or 0),
                int(subscription_count) > 0,
            )
            for deck, card_count, release_number, subscription_count in (
                self.session.execute(statement)
            )
        ], total

    def get_subscription(
        self, user_id: uuid.UUID, deck_id: uuid.UUID
    ) -> DeckSubscription | None:
        return self.session.scalar(
            select(DeckSubscription)
            .options(joinedload(DeckSubscription.deck))
            .where(
                DeckSubscription.user_id == user_id,
                DeckSubscription.deck_id == deck_id,
            )
        )

    def list_active_subscriptions(
        self, user_id: uuid.UUID
    ) -> list[tuple[DeckSubscription, int, int]]:
        active_card_count = (
            select(func.count(DeckCard.id))
            .where(
                DeckCard.deck_id == DeckSubscription.deck_id,
                DeckCard.removed_at.is_(None),
            )
            .correlate(DeckSubscription)
            .scalar_subquery()
        )
        latest_release = (
            select(func.max(Release.release_number))
            .where(Release.deck_id == DeckSubscription.deck_id)
            .correlate(DeckSubscription)
            .scalar_subquery()
        )
        statement = (
            select(DeckSubscription, active_card_count, latest_release)
            .options(joinedload(DeckSubscription.deck))
            .where(
                DeckSubscription.user_id == user_id,
                DeckSubscription.unsubscribed_at.is_(None),
            )
            .order_by(DeckSubscription.created_at.desc(), DeckSubscription.id)
        )
        return [
            (subscription, int(card_count), int(release_number or 0))
            for subscription, card_count, release_number in self.session.execute(
                statement
            )
        ]

    def save_subscription(
        self, subscription: DeckSubscription
    ) -> DeckSubscription:
        self.session.add(subscription)
        self.session.flush()
        return subscription

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
