import math
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.exporters import CsvExport, ReleaseCsvRow, build_release_csv
from app.models import Card, Deck, DeckCard, DeckSubscription, Release, ReleaseItem
from app.models.enums import (
    CardStatus,
    CardVersionStatus,
    DeckStatus,
    ReleaseAction,
)
from app.repositories import DeckRepository
from app.schemas import (
    DeckCreateRequest,
    DeckListResponse,
    DeckResponse,
    DeckSubscriptionListResponse,
    DeckSubscriptionResponse,
    DeckSyncResponse,
    ReleaseListResponse,
    ReleasePublishRequest,
    ReleaseResponse,
    SubscribableDeckListResponse,
)
from app.schemas.decks import (
    AnkiCardFields,
    AnkiDeckManifestResponse,
    AnkiDeckSyncResponse,
    AnkiSyncChangeResponse,
    DeckCardResponse,
    DeckSummaryResponse,
    ReleaseActionCounts,
    ReleaseItemResponse,
    ReleaseSummaryResponse,
    SubscribableDeckResponse,
    SyncChangeResponse,
)


class DeckService:
    CSV_DELIMITERS = {
        "comma": ",",
        "semicolon": ";",
        "tab": "\t",
    }

    def __init__(self, repository: DeckRepository) -> None:
        self.repository = repository
        self.session = repository.session

    def create_deck(self, payload: DeckCreateRequest) -> DeckResponse:
        try:
            with self.session.begin():
                if payload.discipline_id is not None and not (
                    self.repository.discipline_exists(payload.discipline_id)
                ):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Discipline not found",
                    )
                if self.repository.get_by_name(payload.name):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Deck name already exists",
                    )
                deck = self.repository.create(
                    Deck(
                        name=payload.name,
                        discipline_id=payload.discipline_id,
                        description=payload.description,
                        status=DeckStatus.DRAFT,
                    )
                )
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deck could not be created due to a conflict",
            ) from exc
        return self.get_deck(deck.id)

    def list_decks(self, *, page: int, page_size: int) -> DeckListResponse:
        decks, total = self.repository.list_decks(
            page=page,
            page_size=page_size,
        )
        return DeckListResponse(
            items=[
                self._deck_summary(deck, active_card_count)
                for deck, active_card_count in decks
            ],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def list_subscribable_decks(
        self,
        *,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> SubscribableDeckListResponse:
        decks, total = self.repository.list_published_decks(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        return SubscribableDeckListResponse(
            items=[
                SubscribableDeckResponse(
                    **self._deck_summary(deck, active_card_count).model_dump(),
                    latest_release=latest_release,
                    subscribed=subscribed,
                )
                for deck, active_card_count, latest_release, subscribed in decks
            ],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def list_subscriptions(
        self, *, user_id: uuid.UUID
    ) -> DeckSubscriptionListResponse:
        subscriptions = self.repository.list_active_subscriptions(user_id)
        return DeckSubscriptionListResponse(
            items=[
                self._subscription_response(
                    subscription,
                    active_card_count=active_card_count,
                    latest_release=latest_release,
                )
                for subscription, active_card_count, latest_release in subscriptions
            ],
            total=len(subscriptions),
        )

    def subscribe(
        self, deck_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> DeckSubscriptionResponse:
        with self.session.begin():
            deck = self.repository.get_by_id(deck_id, for_update=True)
            if deck is None:
                self._raise_deck_not_found()
            if deck.status != DeckStatus.PUBLISHED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only published decks can be subscribed to",
                )

            subscription = self.repository.get_subscription(user_id, deck.id)
            if subscription is None:
                subscription = self.repository.save_subscription(
                    DeckSubscription(user_id=user_id, deck_id=deck.id)
                )
                subscription.deck = deck
            else:
                subscription.unsubscribed_at = None
            self.session.flush()

        return self._subscription_response(
            subscription,
            active_card_count=self._active_card_count(deck),
            latest_release=self.repository.latest_release_number(deck.id),
        )

    def unsubscribe(
        self, deck_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> DeckSubscriptionResponse:
        with self.session.begin():
            subscription = self.repository.get_subscription(user_id, deck_id)
            if subscription is None or subscription.unsubscribed_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active subscription not found",
                )
            subscription.unsubscribed_at = datetime.now(UTC)
            self.session.flush()

        return self._subscription_response(
            subscription,
            active_card_count=self._active_card_count(subscription.deck),
            latest_release=self.repository.latest_release_number(deck_id),
        )

    def get_deck(self, deck_id: uuid.UUID) -> DeckResponse:
        deck = self.repository.get_by_id(deck_id)
        if deck is None:
            self._raise_deck_not_found()
        return self._deck_response(deck)

    def list_releases(
        self,
        deck_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
    ) -> ReleaseListResponse:
        if not self.repository.deck_exists(deck_id):
            self._raise_deck_not_found()
        releases, total = self.repository.list_releases(
            deck_id,
            page=page,
            page_size=page_size,
        )
        return ReleaseListResponse(
            items=[self._release_summary(release) for release in releases],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
            latest_release=self.repository.latest_release_number(deck_id),
        )

    def sync(
        self,
        deck_id: uuid.UUID,
        *,
        since_release: int,
    ) -> DeckSyncResponse:
        if not self.repository.deck_exists(deck_id):
            self._raise_deck_not_found()

        latest_release = self.repository.latest_release_number(deck_id)
        if since_release > 0 and not self.repository.release_number_exists(
            deck_id, since_release
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release number not found in this deck",
            )

        state: dict[uuid.UUID, uuid.UUID] = {}
        changes: list[SyncChangeResponse] = []
        for item in self.repository.release_items_through(
            deck_id, latest_release
        ):
            old_version_id = state.get(item.card_id)
            new_version_id = item.card_version_id
            if item.release.release_number > since_release:
                changes.append(
                    SyncChangeResponse(
                        release_id=item.release_id,
                        release_number=item.release.release_number,
                        published_at=self._as_utc(item.release.published_at),
                        action=item.action,
                        card_id=item.card_id,
                        public_id=item.card.public_id,
                        old_card_version_id=old_version_id,
                        new_card_version_id=(
                            new_version_id
                            if item.action
                            in (ReleaseAction.ADDED, ReleaseAction.UPDATED)
                            else None
                        ),
                    )
                )

            if item.action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
                if new_version_id is None:
                    raise RuntimeError(
                        "Release item is missing its published card version"
                    )
                state[item.card_id] = new_version_id
            else:
                state.pop(item.card_id, None)

        return DeckSyncResponse(
            deck_id=deck_id,
            from_release=since_release,
            to_release=latest_release,
            has_changes=bool(changes),
            changes=changes,
        )

    def anki_manifest(
        self, deck_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> AnkiDeckManifestResponse:
        deck = self._require_active_subscription(user_id, deck_id).deck
        return AnkiDeckManifestResponse(
            deck_id=deck.id,
            name=deck.name,
            description=deck.description,
            latest_release=self.repository.latest_release_number(deck.id),
            note_type="Anki Concursos Basic",
            fields=["Front", "Back", "Answer", "Explanation"],
            field_mapping={
                "Front": "front_text",
                "Back": "back_text",
                "Answer": "answer_text",
                "Explanation": "explanation_text",
            },
            tags=[f"deck::{deck.id}"],
        )

    def anki_sync(
        self,
        deck_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        since_release: int,
    ) -> AnkiDeckSyncResponse:
        self._require_active_subscription(user_id, deck_id)
        latest_release = self.repository.latest_release_number(deck_id)
        if since_release > 0 and not self.repository.release_number_exists(
            deck_id, since_release
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release number not found in this deck",
            )

        if since_release == 0:
            changes = self._anki_snapshot_changes(deck_id, latest_release)
        else:
            changes = self._anki_delta_changes(deck_id, latest_release, since_release)

        return AnkiDeckSyncResponse(
            deck_id=deck_id,
            from_release=since_release,
            to_release=latest_release,
            has_changes=bool(changes),
            changes=changes,
        )

    def add_card(self, deck_id: uuid.UUID, card_id: uuid.UUID) -> DeckResponse:
        with self.session.begin():
            deck = self.repository.get_by_id(deck_id, for_update=True)
            if deck is None:
                self._raise_deck_not_found()
            card = self.repository.get_card(card_id)
            if card is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Card not found",
                )
            if (
                card.status != CardStatus.PUBLISHED
                or card.current_version is None
                or card.current_version.status != CardVersionStatus.PUBLISHED
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only the current published card version can be added",
                )
            if (
                deck.discipline_id is not None
                and card.discipline_id != deck.discipline_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Card discipline does not match deck discipline",
                )

            membership = self.repository.get_membership(deck.id, card.id)
            if membership is None:
                self.repository.add_membership(
                    DeckCard(
                        deck_id=deck.id,
                        card_id=card.id,
                        card_version_id=card.current_version.id,
                    )
                )
            else:
                if (
                    membership.removed_at is None
                    and membership.card_version_id == card.current_version.id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Card is already current in this deck",
                    )
                membership.card_version_id = card.current_version.id
                membership.removed_at = None
                membership.removal_action = None
                membership.added_at = datetime.now(UTC)
            self.session.flush()
        return self.get_deck(deck_id)

    def remove_card(
        self, deck_id: uuid.UUID, card_id: uuid.UUID, action: str
    ) -> DeckResponse:
        with self.session.begin():
            deck = self.repository.get_by_id(deck_id, for_update=True)
            if deck is None:
                self._raise_deck_not_found()
            membership = self.repository.get_membership(deck.id, card_id)
            if membership is None or membership.removed_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active deck card not found",
                )
            membership.removed_at = datetime.now(UTC)
            membership.removal_action = ReleaseAction(action)
            self.session.flush()
        return self.get_deck(deck_id)

    def publish_release(
        self, deck_id: uuid.UUID, payload: ReleasePublishRequest
    ) -> ReleaseResponse:
        with self.session.begin():
            deck = self.repository.get_by_id(deck_id, for_update=True)
            if deck is None:
                self._raise_deck_not_found()

            previous_state = self._release_state(
                self.repository.release_items(deck.id)
            )
            release_changes = self._release_changes(
                previous_state,
                deck.cards,
            )

            if not release_changes:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Deck has no unpublished changes",
                )

            release = self.repository.create_release(
                Release(
                    deck_id=deck.id,
                    release_number=self.repository.next_release_number(deck.id),
                    description=payload.description,
                )
            )
            self.repository.create_release_items(
                [
                    ReleaseItem(
                        release_id=release.id,
                        card_id=card_id,
                        card_version_id=card_version_id,
                        action=action,
                    )
                    for card_id, card_version_id, action in sorted(
                        release_changes, key=lambda change: str(change[0])
                    )
                ]
            )
            deck.status = DeckStatus.PUBLISHED
            self.session.flush()

        stored_release = self.repository.get_release(release.id)
        if stored_release is None:
            raise RuntimeError("Published release could not be reloaded")
        return self._release_response(stored_release)

    def export_release_csv(
        self,
        deck_id: uuid.UUID,
        release_id: uuid.UUID,
        *,
        delimiter_name: str,
        include_tags: bool,
    ) -> tuple[Release, CsvExport]:
        release = self.repository.get_release(release_id)
        if release is None or release.deck_id != deck_id:
            if not self.repository.deck_exists(deck_id):
                self._raise_deck_not_found()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Release not found in this deck",
            )

        snapshot: dict[uuid.UUID, ReleaseItem] = {}
        for item in self.repository.release_items_through(
            deck_id, release.release_number
        ):
            if item.action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
                if item.card_version is None:
                    raise RuntimeError(
                        "Release item is missing its published card version"
                    )
                snapshot[item.card_id] = item
            else:
                snapshot.pop(item.card_id, None)

        rows = [
            ReleaseCsvRow(
                public_id=item.card.public_id,
                card_id=item.card_id,
                card_version_id=item.card_version.id,
                front_text=item.card_version.front_text,
                back_text=item.card_version.back_text,
                answer_text=item.card_version.answer_text,
                explanation_text=item.card_version.explanation_text,
                tags=(
                    self._stable_tags(release.deck_id, item.card)
                    if include_tags
                    else ""
                ),
            )
            for item in snapshot.values()
            if item.card_version is not None
        ]
        return release, build_release_csv(
            rows,
            delimiter=self.CSV_DELIMITERS[delimiter_name],
        )

    @staticmethod
    def _stable_tags(deck_id: uuid.UUID, card: Card) -> str:
        return " ".join(
            (
                f"deck::{deck_id}",
                f"card::{card.public_id}",
            )
        )

    def _require_active_subscription(
        self, user_id: uuid.UUID, deck_id: uuid.UUID
    ) -> DeckSubscription:
        subscription = self.repository.get_subscription(user_id, deck_id)
        if subscription is None or subscription.unsubscribed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscribe to this deck before syncing it",
            )
        if subscription.deck.status != DeckStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deck is not published",
            )
        return subscription

    def _anki_snapshot_changes(
        self, deck_id: uuid.UUID, latest_release: int
    ) -> list[AnkiSyncChangeResponse]:
        snapshot: dict[uuid.UUID, ReleaseItem] = {}
        for item in self.repository.release_items_through(deck_id, latest_release):
            if item.action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
                if item.card_version is None:
                    raise RuntimeError(
                        "Release item is missing its published card version"
                    )
                snapshot[item.card_id] = item
            else:
                snapshot.pop(item.card_id, None)

        return [
            self._anki_change_response(
                item,
                action=ReleaseAction.ADDED,
                old_card_version_id=None,
            )
            for item in sorted(
                snapshot.values(),
                key=lambda value: value.card.public_id,
            )
        ]

    def _anki_delta_changes(
        self,
        deck_id: uuid.UUID,
        latest_release: int,
        since_release: int,
    ) -> list[AnkiSyncChangeResponse]:
        state: dict[uuid.UUID, uuid.UUID] = {}
        changes: list[AnkiSyncChangeResponse] = []
        for item in self.repository.release_items_through(deck_id, latest_release):
            old_version_id = state.get(item.card_id)
            if item.release.release_number > since_release:
                changes.append(
                    self._anki_change_response(
                        item,
                        action=item.action,
                        old_card_version_id=old_version_id,
                    )
                )

            if item.action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
                if item.card_version_id is None:
                    raise RuntimeError(
                        "Release item is missing its published card version"
                    )
                state[item.card_id] = item.card_version_id
            else:
                state.pop(item.card_id, None)
        return changes

    def _anki_change_response(
        self,
        item: ReleaseItem,
        *,
        action: ReleaseAction,
        old_card_version_id: uuid.UUID | None,
    ) -> AnkiSyncChangeResponse:
        fields = None
        new_card_version_id = None
        if action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
            if item.card_version is None:
                raise RuntimeError(
                    "Release item is missing its published card version"
                )
            new_card_version_id = item.card_version.id
            fields = AnkiCardFields(
                Front=item.card_version.front_text,
                Back=item.card_version.back_text,
                Answer=item.card_version.answer_text,
                Explanation=item.card_version.explanation_text,
            )

        return AnkiSyncChangeResponse(
            release_id=item.release_id,
            release_number=item.release.release_number,
            published_at=self._as_utc(item.release.published_at),
            action=action,
            card_id=item.card_id,
            public_id=item.card.public_id,
            old_card_version_id=old_card_version_id,
            new_card_version_id=new_card_version_id,
            fields=fields,
            tags=[f"deck::{item.release.deck_id}", f"card::{item.card.public_id}"],
        )

    @staticmethod
    def _active_card_count(deck: Deck) -> int:
        return sum(1 for membership in deck.cards if membership.removed_at is None)

    @staticmethod
    def _subscription_response(
        subscription: DeckSubscription,
        *,
        active_card_count: int,
        latest_release: int,
    ) -> DeckSubscriptionResponse:
        return DeckSubscriptionResponse(
            subscription_id=subscription.id,
            deck_id=subscription.deck_id,
            deck_name=subscription.deck.name,
            latest_release=latest_release,
            active_card_count=active_card_count,
            subscribed_at=subscription.created_at,
            unsubscribed_at=subscription.unsubscribed_at,
        )

    @staticmethod
    def _deck_response(deck: Deck) -> DeckResponse:
        active_cards = [
            DeckCardResponse(
                card_id=membership.card_id,
                public_id=membership.card.public_id,
                card_version_id=membership.card_version_id,
                version_number=membership.card_version.version_number,
                added_at=membership.added_at,
            )
            for membership in deck.cards
            if membership.removed_at is None
        ]
        active_cards.sort(key=lambda item: item.public_id)
        return DeckResponse(
            deck_id=deck.id,
            name=deck.name,
            discipline_id=deck.discipline_id,
            description=deck.description,
            status=deck.status,
            cards=active_cards,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )

    @staticmethod
    def _deck_summary(
        deck: Deck,
        active_card_count: int,
    ) -> DeckSummaryResponse:
        return DeckSummaryResponse(
            deck_id=deck.id,
            name=deck.name,
            discipline_id=deck.discipline_id,
            description=deck.description,
            status=deck.status,
            active_card_count=active_card_count,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )

    @staticmethod
    def _release_state(
        items: list[ReleaseItem],
    ) -> dict[uuid.UUID, uuid.UUID]:
        state: dict[uuid.UUID, uuid.UUID] = {}
        for item in items:
            if item.action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
                if item.card_version_id is None:
                    raise RuntimeError(
                        "Release item is missing its published card version"
                    )
                state[item.card_id] = item.card_version_id
            else:
                state.pop(item.card_id, None)
        return state

    @staticmethod
    def _release_changes(
        previous_state: dict[uuid.UUID, uuid.UUID],
        memberships: list[DeckCard],
    ) -> list[tuple[uuid.UUID, uuid.UUID | None, ReleaseAction]]:
        active = {
            membership.card_id: membership
            for membership in memberships
            if membership.removed_at is None
        }
        all_memberships = {
            membership.card_id: membership for membership in memberships
        }
        changes: list[tuple[uuid.UUID, uuid.UUID | None, ReleaseAction]] = []
        for card_id, previous_version_id in previous_state.items():
            membership = active.get(card_id)
            if membership is None:
                removed = all_memberships.get(card_id)
                action = (
                    removed.removal_action
                    if removed is not None and removed.removal_action is not None
                    else ReleaseAction.REMOVED
                )
                changes.append((card_id, None, action))
            elif membership.card_version_id != previous_version_id:
                changes.append(
                    (
                        card_id,
                        membership.card_version_id,
                        ReleaseAction.UPDATED,
                    )
                )
        for card_id, membership in active.items():
            if card_id not in previous_state:
                changes.append(
                    (card_id, membership.card_version_id, ReleaseAction.ADDED)
                )
        return changes

    @staticmethod
    def _release_response(release: Release) -> ReleaseResponse:
        items = [
            ReleaseItemResponse(
                action=item.action,
                card_id=item.card_id,
                public_id=item.card.public_id,
                card_version_id=item.card_version_id,
            )
            for item in release.items
        ]
        items.sort(key=lambda item: item.public_id)
        return ReleaseResponse(
            release_id=release.id,
            deck_id=release.deck_id,
            release_number=release.release_number,
            published_at=DeckService._as_utc(release.published_at),
            description=release.description,
            items=items,
        )

    @staticmethod
    def _release_summary(release: Release) -> ReleaseSummaryResponse:
        counts = {
            action: sum(1 for item in release.items if item.action == action)
            for action in ReleaseAction
        }
        return ReleaseSummaryResponse(
            release_id=release.id,
            deck_id=release.deck_id,
            release_number=release.release_number,
            published_at=DeckService._as_utc(release.published_at),
            description=release.description,
            item_count=len(release.items),
            actions=ReleaseActionCounts(
                added=counts[ReleaseAction.ADDED],
                updated=counts[ReleaseAction.UPDATED],
                removed=counts[ReleaseAction.REMOVED],
                deprecated=counts[ReleaseAction.DEPRECATED],
            ),
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _raise_deck_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found",
        )
