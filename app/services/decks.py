import hashlib
import json
import math
import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.honeybadger import notify_exception
from app.exporters import CsvExport, ReleaseCsvRow, build_release_csv
from app.models import (
    Card,
    CardVersion,
    Deck,
    DeckCard,
    DeckSnapshot,
    DeckTemplate,
    DeckTemplateVersion,
    DeckSubscription,
    Release,
    ReleaseItem,
)
from app.models.enums import (
    CardKind,
    CardStatus,
    CardVersionStatus,
    DeckStatus,
    ReleaseAction,
)
from app.repositories import CardRepository, DeckRepository
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
    AnkiDeckManifestResponse,
    AnkiDeckSyncResponse,
    AnkiDeckTemplatePayload,
    AnkiDeckUploadItemResponse,
    AnkiDeckUploadRequest,
    AnkiDeckUploadResponse,
    AnkiSyncChangeResponse,
    DeckCardResponse,
    DeckSummaryResponse,
    ReleaseActionCounts,
    ReleaseItemResponse,
    ReleaseSummaryResponse,
    SubscribableDeckResponse,
    SyncChangeResponse,
)
from app.services.cards import CLOZE_PATTERN


class DeckService:
    CSV_DELIMITERS = {
        "comma": ",",
        "semicolon": ";",
        "tab": "\t",
    }
    ANKI_NOTE_TYPES = {
        CardKind.BASIC: {
            "note_type": "Anki Concursos Basic",
            "fields": ["Front", "Back", "Answer", "Explanation"],
            "field_mapping": {
                "Front": "front_text",
                "Back": "back_text",
                "Answer": "answer_text",
                "Explanation": "explanation_text",
            },
        },
        CardKind.CLOZE: {
            "note_type": "Anki Concursos Cloze",
            "fields": ["Text", "Extra", "Answer", "Explanation"],
            "field_mapping": {
                "Text": "front_text",
                "Extra": "back_text",
                "Answer": "answer_text",
                "Explanation": "explanation_text",
            },
        },
    }

    def __init__(self, repository: DeckRepository) -> None:
        self.repository = repository
        self.session = repository.session
        self.card_repository = CardRepository(self.session)

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
        try:
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
        except Exception as exc:
            notify_exception(
                exc,
                context={
                    "operation": "sync",
                    "deck_id": str(deck_id),
                    "since_release": since_release,
                },
                tags=["deck", "sync"],
            )
            raise

    def anki_manifest(
        self, deck_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> AnkiDeckManifestResponse:
        deck = self._require_active_subscription(user_id, deck_id).deck
        templates = self._manifest_templates_from_db(deck.id)
        if not templates:
            snapshot = self.repository.latest_snapshot(deck.id)
            templates = self._manifest_templates(snapshot)
        primary_template = templates[0] if templates else None
        return AnkiDeckManifestResponse(
            deck_id=deck.id,
            name=deck.name,
            description=deck.description,
            latest_release=self.repository.latest_release_number(deck.id),
            note_type=(
                primary_template.note_type
                if primary_template is not None
                else "Anki Concursos Basic"
            ),
            fields=(
                primary_template.fields
                if primary_template is not None
                else ["Front", "Back", "Answer", "Explanation"]
            ),
            field_mapping=(
                primary_template.field_mapping
                if primary_template is not None
                else {
                    "Front": "front_text",
                    "Back": "back_text",
                    "Answer": "answer_text",
                    "Explanation": "explanation_text",
                }
            ),
            supported_note_types={
                kind.value: {
                    "note_type": config["note_type"],
                    "fields": config["fields"],
                    "field_mapping": config["field_mapping"],
                }
                for kind, config in self.ANKI_NOTE_TYPES.items()
            },
            templates=templates,
            tags=[f"deck::{deck.id}"],
        )

    def anki_sync(
        self,
        deck_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        since_release: int,
        page: int | None = None,
        page_size: int | None = None,
    ) -> AnkiDeckSyncResponse:
        try:
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
                changes = self._anki_delta_changes(
                    deck_id, latest_release, since_release
                )

            total_changes = len(changes)
            pages = None
            if page is not None or page_size is not None:
                page = page or 1
                page_size = page_size or 500
                pages = math.ceil(total_changes / page_size) if total_changes else 0
                start = (page - 1) * page_size
                changes = changes[start : start + page_size]

            return AnkiDeckSyncResponse(
                deck_id=deck_id,
                from_release=since_release,
                to_release=latest_release,
                has_changes=total_changes > 0,
                changes=changes,
                page=page,
                pages=pages,
                total_changes=total_changes if page is not None else None,
            )
        except Exception as exc:
            notify_exception(
                exc,
                context={
                    "operation": "anki_sync",
                    "deck_id": str(deck_id),
                    "since_release": since_release,
                    "page": page,
                    "page_size": page_size,
                    "user_id": str(user_id),
                },
                tags=["addon", "sync"],
            )
            raise

    def upload_anki_deck(  # noqa: C901 - orchestration across upload, versioning and release
        self,
        payload: AnkiDeckUploadRequest,
        *,
        uploaded_by: str,
    ) -> AnkiDeckUploadResponse:
        deck: Deck | None = None
        snapshot: DeckSnapshot | None = None
        release: Release | None = None
        items: list[AnkiDeckUploadItemResponse] = []
        created_cards = 0
        reused_cards = 0
        updated_cards = 0
        try:
            with self.session.begin():
                deck = self.repository.get_by_name(payload.deck_name)
                if deck is None:
                    deck = self.repository.create(
                        Deck(
                            name=payload.deck_name,
                            discipline_id=None,
                            description=payload.description,
                            status=DeckStatus.DRAFT,
                        )
                    )
                else:
                    if deck.status == DeckStatus.ARCHIVED:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Archived decks cannot receive uploads",
                        )
                    if payload.description is not None:
                        deck.description = payload.description

                snapshot = self.repository.create_snapshot(
                    DeckSnapshot(
                        deck_id=deck.id,
                        uploaded_by=uploaded_by,
                        source_name=payload.source_name,
                        note_count=len(payload.notes),
                        payload_json=payload.model_dump(mode="json"),
                    )
                )

                template_map: dict[tuple[str, str], AnkiDeckTemplatePayload] = {}
                templates_by_note_type: dict[str, list[AnkiDeckTemplatePayload]] = {}
                for template in payload.templates:
                    template_key = self._template_key_for_upload(
                        deck.id,
                        template.template_name,
                        template.note_type,
                    )
                    deck_template = self.repository.get_template_by_key(
                        deck.id,
                        template_key,
                    )
                    template_hash = self._template_content_hash(template)
                    if deck_template is None:
                        deck_template = self.repository.create_template(
                            DeckTemplate(
                                deck_id=deck.id,
                                template_key=template_key,
                                template_name=template.template_name,
                                note_type=template.note_type,
                                card_kind=template.card_kind,
                            )
                        )
                    template_version_number = self.repository.next_template_version_number(
                        deck_template.id
                    )
                    if (
                        deck_template.current_version is not None
                        and deck_template.current_version.content_hash == template_hash
                    ):
                        template_version_number = deck_template.current_version.version_number

                    if (
                        deck_template.current_version is None
                        or deck_template.current_version.content_hash != template_hash
                    ):
                        deck_template_version = self.repository.create_template_version(
                            DeckTemplateVersion(
                                deck_template_id=deck_template.id,
                                version_number=template_version_number,
                                fields=list(template.fields),
                                field_mapping=dict(template.field_mapping),
                                front_html=template.front_html,
                                back_html=template.back_html,
                                styling_css=template.styling_css,
                                content_hash=template_hash,
                                status="published",
                                created_by=uploaded_by,
                            )
                        )
                        deck_template.current_version_id = deck_template_version.id
                    deck_template.template_name = template.template_name
                    deck_template.note_type = template.note_type
                    deck_template.card_kind = template.card_kind
                    normalized_note_type = self._normalize_upload_key(
                        template.note_type
                    )
                    normalized_template_name = self._normalize_upload_key(
                        template.template_name
                    )
                    template_map[
                        (normalized_note_type, normalized_template_name)
                    ] = template
                    templates_by_note_type.setdefault(
                        normalized_note_type,
                        [],
                    ).append(template)

                for note_index, note in enumerate(payload.notes, start=1):
                    normalized_note_type = self._normalize_upload_key(note.note_type)
                    normalized_template_name = self._normalize_upload_key(
                        note.template_name
                    )
                    template = None
                    if normalized_template_name:
                        template = template_map.get(
                            (normalized_note_type, normalized_template_name)
                        )
                    if template is None:
                        candidates = templates_by_note_type.get(
                            normalized_note_type,
                            [],
                        )
                        if len(candidates) == 1:
                            template = candidates[0]
                    if template is None and normalized_template_name:
                        template = next(
                            (
                                item
                                for item in payload.templates
                                if self._normalize_upload_key(item.template_name)
                                == normalized_template_name
                            ),
                            None,
                        )
                    if template is None:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=(
                                f"Template not found for note_type {note.note_type}"
                                + (
                                    f" and template_name {note.template_name}"
                                    if note.template_name
                                    else ""
                                )
                            ),
                        )

                    note_card_kind = self._parse_card_kind(note.card_kind)
                    template_card_kind = self._parse_card_kind(template.card_kind)
                    if note_card_kind != template_card_kind:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=(
                                "Note card_kind does not match the declared "
                                f"template for {note.note_type}"
                            ),
                        )

                    content = self._map_upload_content(
                        note.fields,
                        template.field_mapping,
                    )
                    content = self._complete_upload_content(
                        note_card_kind,
                        content,
                        note.fields,
                    )
                    content_hash = self._upload_content_hash(
                        card_kind=note_card_kind,
                        note_type=note.note_type,
                        template_name=template.template_name,
                        fields=note.fields,
                        template=template,
                        tags=note.tags,
                    )
                    canonical_key = self._canonical_key_for_deck_upload(
                        deck.id,
                        note_type=note.note_type,
                        template_name=template.template_name,
                        content_hash=content_hash,
                        source_note_id=note.source_note_id,
                        source_note_guid=note.source_note_guid,
                    )

                    card = self.card_repository.get_by_canonical_key(canonical_key)
                    if card is None:
                        card = self.card_repository.create_card(
                        Card(
                            canonical_key=canonical_key,
                            card_kind=note_card_kind,
                            discipline_id=None,
                            topic_id=None,
                            status=CardStatus.PUBLISHED,
                        )
                    )
                        version = self.card_repository.create_version(
                            CardVersion(
                                card_id=card.id,
                                version_number=1,
                                front_text=content["front_text"],
                                back_text=content["back_text"],
                                answer_text=content["answer_text"],
                                explanation_text=content["explanation_text"],
                                note_type=note.note_type,
                                template_name=template.template_name,
                                anki_fields=dict(note.fields),
                                anki_template=template.model_dump(mode="json"),
                                anki_tags=list(note.tags),
                                source_note_id=note.source_note_id,
                                source_note_guid=note.source_note_guid,
                                source_deck_path=(
                                    note.source_deck_path
                                    or payload.source_deck_path
                                ),
                                change_reason="Upload do baralho Anki",
                                created_by=uploaded_by,
                                status=CardVersionStatus.PUBLISHED,
                                content_hash=content_hash,
                            )
                        )
                        card.current_version_id = version.id
                        created_cards += 1
                        item_status = "created"
                    else:
                        if card.current_version is None:
                            raise RuntimeError(
                                "Existing card is missing its current version"
                            )
                        if card.current_version.content_hash == content_hash:
                            version = card.current_version
                            reused_cards += 1
                            item_status = "reused"
                        else:
                            version = self.card_repository.create_version(
                                CardVersion(
                                    card_id=card.id,
                                    version_number=(
                                        self.card_repository.next_version_number(
                                            card.id
                                        )
                                    ),
                                    front_text=content["front_text"],
                                    back_text=content["back_text"],
                                    answer_text=content["answer_text"],
                                    explanation_text=content["explanation_text"],
                                    note_type=note.note_type,
                                    template_name=template.template_name,
                                    anki_fields=dict(note.fields),
                                    anki_template=template.model_dump(mode="json"),
                                    anki_tags=list(note.tags),
                                    source_note_id=note.source_note_id,
                                    source_note_guid=note.source_note_guid,
                                    source_deck_path=(
                                        note.source_deck_path
                                        or payload.source_deck_path
                                    ),
                                    change_reason="Upload atualizado do baralho Anki",
                                    created_by=uploaded_by,
                                    status=CardVersionStatus.PUBLISHED,
                                    content_hash=content_hash,
                                )
                            )
                            card.current_version_id = version.id
                            updated_cards += 1
                            item_status = "updated"

                    membership = self.repository.get_membership(deck.id, card.id)
                    if membership is None:
                        self.repository.add_membership(
                            DeckCard(
                                deck_id=deck.id,
                                card_id=card.id,
                                card_version_id=version.id,
                            )
                        )
                    else:
                        membership.card_version_id = version.id
                        membership.removed_at = None
                        membership.removal_action = None
                        membership.added_at = datetime.now(UTC)

                    items.append(
                        AnkiDeckUploadItemResponse(
                            note_index=note_index,
                            status=item_status,
                            canonical_key=canonical_key,
                            card_id=card.id,
                            public_id=card.public_id,
                            card_version_id=version.id,
                            note_type=template.note_type,
                            card_kind=note_card_kind.value,
                        )
                    )

                self.session.flush()
                deck = self.repository.get_by_id(deck.id, for_update=True)
                if deck is None:
                    raise RuntimeError("Uploaded deck could not be reloaded")

                if payload.publish_release:
                    previous_state = self._release_state(
                        self.repository.release_items(deck.id)
                    )
                    release_changes = self._release_changes(
                        previous_state,
                        deck.cards,
                    )
                    if release_changes:
                        release = self.repository.create_release(
                            Release(
                                deck_id=deck.id,
                                release_number=self.repository.next_release_number(
                                    deck.id
                                ),
                                description=(
                                    payload.description
                                    or "Upload completo do baralho Anki"
                                ),
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
                                    release_changes,
                                    key=lambda change: str(change[0]),
                                )
                            ]
                        )
                        deck.status = DeckStatus.PUBLISHED
                        snapshot.release_id = release.id
                        self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            notify_exception(
                exc,
                context={
                    "operation": "upload_anki_deck",
                    "deck_name": payload.deck_name,
                    "uploaded_by": uploaded_by,
                    "source_name": payload.source_name,
                },
                tags=["addon", "upload", "database"],
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deck upload could not be created due to a data conflict",
            ) from exc
        except Exception as exc:
            self.session.rollback()
            notify_exception(
                exc,
                context={
                    "operation": "upload_anki_deck",
                    "deck_name": payload.deck_name,
                    "uploaded_by": uploaded_by,
                    "source_name": payload.source_name,
                    "notes": len(payload.notes),
                },
                tags=["addon", "upload"],
            )
            raise

        assert deck is not None
        assert snapshot is not None
        latest_release = self.repository.latest_release_number(deck.id)
        return AnkiDeckUploadResponse(
            deck_id=deck.id,
            deck_name=deck.name,
            snapshot_id=snapshot.id,
            release_id=release.id if release is not None else None,
            latest_release=latest_release,
            published=release is not None,
            total_notes=len(items),
            created_cards=created_cards,
            reused_cards=reused_cards,
            updated_cards=updated_cards,
            items=items,
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
        try:
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
        except Exception as exc:
            notify_exception(
                exc,
                context={
                    "operation": "publish_release",
                    "deck_id": str(deck_id),
                    "description": payload.description,
                },
                tags=["deck", "release"],
            )
            raise

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
                card_kind=item.card.card_kind.value,
                note_type=str(
                    self.ANKI_NOTE_TYPES[item.card.card_kind]["note_type"]
                ),
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

    @staticmethod
    def _manifest_templates(
        snapshot: DeckSnapshot | None,
    ) -> list[AnkiDeckTemplatePayload]:
        if snapshot is None:
            return []
        raw_templates = snapshot.payload_json.get("templates", [])
        templates: list[AnkiDeckTemplatePayload] = []
        for raw_template in raw_templates:
            try:
                templates.append(AnkiDeckTemplatePayload.model_validate(raw_template))
            except Exception:
                continue
        return templates

    def _manifest_templates_from_db(
        self,
        deck_id: uuid.UUID,
    ) -> list[AnkiDeckTemplatePayload]:
        templates: list[AnkiDeckTemplatePayload] = []
        for deck_template in self.repository.list_templates(deck_id):
            current_version = deck_template.current_version
            if current_version is None:
                continue
            templates.append(
                AnkiDeckTemplatePayload(
                    template_name=deck_template.template_name,
                    note_type=deck_template.note_type,
                    card_kind=deck_template.card_kind,
                    fields=list(current_version.fields),
                    field_mapping=dict(current_version.field_mapping),
                    front_html=current_version.front_html,
                    back_html=current_version.back_html,
                    styling_css=current_version.styling_css,
                )
            )
        return templates

    @staticmethod
    def _template_key_for_upload(
        deck_id: uuid.UUID,
        template_name: str,
        note_type: str,
    ) -> str:
        normalized_name = DeckService._normalize_upload_key(template_name)
        normalized_note_type = DeckService._normalize_upload_key(note_type)
        raw_key = f"{deck_id}:{normalized_note_type}:{normalized_name}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _template_content_hash(template: AnkiDeckTemplatePayload) -> str:
        payload = {
            "template_name": template.template_name,
            "note_type": template.note_type,
            "card_kind": template.card_kind.value
            if isinstance(template.card_kind, CardKind)
            else str(template.card_kind),
            "fields": list(template.fields),
            "field_mapping": dict(sorted(template.field_mapping.items())),
            "front_html": template.front_html,
            "back_html": template.back_html,
            "styling_css": template.styling_css,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_card_kind(value: CardKind | str) -> CardKind:
        if isinstance(value, CardKind):
            return value
        normalized = value.strip().lower()
        if normalized in {"basic", "anki concursos basic"}:
            return CardKind.BASIC
        if normalized in {"cloze", "anki concursos cloze"}:
            return CardKind.CLOZE
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="card_kind must be basic or cloze",
        )

    @staticmethod
    def _validate_content_for_kind(card_kind: CardKind, front_text: str) -> None:
        if card_kind == CardKind.CLOZE and not CLOZE_PATTERN.search(front_text):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Cloze cards must include {{c1::...}} markup in front_text",
            )

    @staticmethod
    def _map_upload_content(
        fields: dict[str, str],
        field_mapping: dict[str, str],
    ) -> dict[str, str]:
        reverse_mapping = {
            target.strip(): source.strip()
            for source, target in field_mapping.items()
            if source and target
        }
        canonical_fields: dict[str, str] = {}
        canonical_names = (
            "front_text",
            "back_text",
            "answer_text",
            "explanation_text",
        )
        for canonical_name in canonical_names:
            source_name = reverse_mapping.get(canonical_name, canonical_name)
            raw_value = fields.get(source_name, "")
            value = raw_value.strip() if isinstance(raw_value, str) else ""
            canonical_fields[canonical_name] = value
        if not canonical_fields["front_text"]:
            canonical_fields["front_text"] = next(
                (
                    value.strip()
                    for value in fields.values()
                    if isinstance(value, str) and value.strip()
                ),
                "",
            )
        if not canonical_fields["front_text"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Uploaded note has no non-empty fields",
            )
        canonical_fields.setdefault("back_text", "")
        canonical_fields.setdefault("answer_text", "")
        canonical_fields.setdefault("explanation_text", "")
        return canonical_fields

    @staticmethod
    def _complete_upload_content(
        card_kind: CardKind,
        content: dict[str, str],
        raw_fields: dict[str, str],
    ) -> dict[str, str]:
        completed = dict(content)
        front_text = completed.get("front_text", "").strip()

        if card_kind == CardKind.CLOZE and not CLOZE_PATTERN.search(front_text):
            cloze_source = next(
                (
                    value.strip()
                    for value in raw_fields.values()
                    if isinstance(value, str) and CLOZE_PATTERN.search(value)
                ),
                "",
            )
            if cloze_source:
                original_front_text = front_text
                completed["front_text"] = cloze_source
                front_text = cloze_source
                if not completed.get("back_text", "").strip():
                    completed["back_text"] = original_front_text or cloze_source
                if not completed.get("answer_text", "").strip():
                    completed["answer_text"] = (
                        completed["back_text"] or original_front_text or cloze_source
                    )
                if not completed.get("explanation_text", "").strip():
                    completed["explanation_text"] = (
                        original_front_text
                        or completed["back_text"]
                        or completed["answer_text"]
                        or cloze_source
                    )

        if not completed.get("back_text", "").strip():
            completed["back_text"] = (
                completed.get("answer_text", "").strip()
                or completed.get("explanation_text", "").strip()
                or front_text
            )
        if not completed.get("answer_text", "").strip():
            completed["answer_text"] = (
                completed.get("back_text", "").strip() or front_text
            )
        if not completed.get("explanation_text", "").strip():
            completed["explanation_text"] = (
                completed.get("back_text", "").strip()
                or completed.get("answer_text", "").strip()
                or front_text
            )
        return completed

    @staticmethod
    def _upload_content_hash(
        *,
        card_kind: CardKind,
        note_type: str,
        template_name: str,
        fields: dict[str, str],
        template: AnkiDeckTemplatePayload,
        tags: list[str],
    ) -> str:
        canonical_content = json.dumps(
            {
                "card_kind": card_kind.value,
                "fields": fields,
                "note_type": note_type,
                "tags": tags,
                "template": template.model_dump(mode="json"),
                "template_name": template_name,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()

    @staticmethod
    def _canonical_key_for_deck_upload(
        deck_id: uuid.UUID,
        *,
        note_type: str,
        template_name: str,
        content_hash: str,
        source_note_id: str | None = None,
        source_note_guid: str | None = None,
    ) -> str:
        source_identity = source_note_guid or source_note_id
        if source_identity:
            source_key = re.sub(
                r"[^a-z0-9]",
                "",
                source_identity.lower(),
            )[:120]
            template_key = re.sub(
                r"[^a-z0-9]",
                "",
                DeckService._normalize_upload_key(template_name),
            )[:80]
            return f"deck-{deck_id.hex}-anki-note-{source_key}-{template_key}"
        sanitized_hash = re.sub(r"[^a-z0-9]", "", content_hash.lower())[:48]
        note_key = re.sub(
            r"[^a-z0-9]",
            "",
            DeckService._normalize_upload_key(note_type),
        )
        template_key = re.sub(
            r"[^a-z0-9]",
            "",
            DeckService._normalize_upload_key(template_name),
        )
        return f"deck-{deck_id.hex}-{note_key}-{template_key}-{sanitized_hash}"

    @staticmethod
    def _normalize_upload_key(value: str | None) -> str:
        if not value:
            return ""
        cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", value)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.lower()

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
        template = None
        new_card_version_id = None
        card_kind = None
        note_type = None
        template_name = None
        source_note_id = None
        source_note_guid = None
        source_deck_path = None
        tags = [f"deck::{item.release.deck_id}", f"card::{item.card.public_id}"]
        if action in (ReleaseAction.ADDED, ReleaseAction.UPDATED):
            if item.card_version is None:
                raise RuntimeError(
                    "Release item is missing its published card version"
                )
            new_card_version_id = item.card_version.id
            card_kind = item.card.card_kind
            note_type = item.card_version.note_type
            template_name = item.card_version.template_name
            template = item.card_version.anki_template or None
            source_note_id = item.card_version.source_note_id
            source_note_guid = item.card_version.source_note_guid
            source_deck_path = item.card_version.source_deck_path
            if item.card_version.anki_fields:
                fields = dict(item.card_version.anki_fields)
                tags = list(item.card_version.anki_tags or []) + tags
            else:
                note_config = self.ANKI_NOTE_TYPES[card_kind]
                note_type = str(note_config["note_type"])
                field_mapping = note_config["field_mapping"]
                fields = {
                    field_name: getattr(item.card_version, source_column)
                    for field_name, source_column in field_mapping.items()
                }

        return AnkiSyncChangeResponse(
            release_id=item.release_id,
            release_number=item.release.release_number,
            published_at=self._as_utc(item.release.published_at),
            action=action,
            card_id=item.card_id,
            public_id=item.card.public_id,
            old_card_version_id=old_card_version_id,
            new_card_version_id=new_card_version_id,
            card_kind=card_kind.value if card_kind is not None else None,
            note_type=note_type,
            template_name=template_name,
            fields=fields,
            template=template,
            source_note_id=source_note_id,
            source_note_guid=source_note_guid,
            source_deck_path=source_deck_path,
            tags=list(dict.fromkeys(tags)),
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
