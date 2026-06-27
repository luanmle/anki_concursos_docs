import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import CardKind, DeckStatus, ReleaseAction


class DeckCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    discipline_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class DeckCardAddRequest(BaseModel):
    card_id: uuid.UUID


class DeckCardRemoveRequest(BaseModel):
    action: Literal["removed", "deprecated"] = "removed"


class DeckCardResponse(BaseModel):
    card_id: uuid.UUID
    public_id: str
    card_version_id: uuid.UUID
    version_number: int
    added_at: datetime


class DeckResponse(BaseModel):
    deck_id: uuid.UUID
    name: str
    discipline_id: uuid.UUID | None
    description: str | None
    status: DeckStatus
    cards: list[DeckCardResponse]
    created_at: datetime
    updated_at: datetime


class DeckSummaryResponse(BaseModel):
    deck_id: uuid.UUID
    name: str
    discipline_id: uuid.UUID | None
    description: str | None
    status: DeckStatus
    active_card_count: int
    created_at: datetime
    updated_at: datetime


class DeckListResponse(BaseModel):
    items: list[DeckSummaryResponse]
    page: int
    page_size: int
    total: int
    pages: int


class SubscribableDeckResponse(DeckSummaryResponse):
    latest_release: int
    subscribed: bool


class SubscribableDeckListResponse(BaseModel):
    items: list[SubscribableDeckResponse]
    page: int
    page_size: int
    total: int
    pages: int


class DeckSubscriptionResponse(BaseModel):
    subscription_id: uuid.UUID
    deck_id: uuid.UUID
    deck_name: str
    latest_release: int
    active_card_count: int
    subscribed_at: datetime
    unsubscribed_at: datetime | None


class DeckSubscriptionListResponse(BaseModel):
    items: list[DeckSubscriptionResponse]
    total: int


class ReleasePublishRequest(BaseModel):
    description: str | None = Field(default=None, max_length=5000)


class ReleaseItemResponse(BaseModel):
    action: ReleaseAction
    card_id: uuid.UUID
    public_id: str
    card_version_id: uuid.UUID | None


class ReleaseResponse(BaseModel):
    release_id: uuid.UUID
    deck_id: uuid.UUID
    release_number: int
    published_at: datetime
    description: str | None
    items: list[ReleaseItemResponse]


class ReleaseActionCounts(BaseModel):
    added: int
    updated: int
    removed: int
    deprecated: int


class ReleaseSummaryResponse(BaseModel):
    release_id: uuid.UUID
    deck_id: uuid.UUID
    release_number: int
    published_at: datetime
    description: str | None
    item_count: int
    actions: ReleaseActionCounts


class ReleaseListResponse(BaseModel):
    items: list[ReleaseSummaryResponse]
    page: int
    page_size: int
    total: int
    pages: int
    latest_release: int


class SyncChangeResponse(BaseModel):
    release_id: uuid.UUID
    release_number: int
    published_at: datetime
    action: ReleaseAction
    card_id: uuid.UUID
    public_id: str
    old_card_version_id: uuid.UUID | None
    new_card_version_id: uuid.UUID | None


class DeckSyncResponse(BaseModel):
    deck_id: uuid.UUID
    from_release: int
    to_release: int
    has_changes: bool
    changes: list[SyncChangeResponse]


class AnkiDeckManifestResponse(BaseModel):
    deck_id: uuid.UUID
    name: str
    description: str | None
    latest_release: int
    note_type: str
    fields: list[str]
    field_mapping: dict[str, str]
    supported_note_types: dict[str, dict[str, Any]]
    templates: list["AnkiDeckTemplatePayload"] = Field(default_factory=list)
    tags: list[str]


class AnkiSyncChangeResponse(BaseModel):
    release_id: uuid.UUID
    release_number: int
    published_at: datetime
    action: ReleaseAction
    card_id: uuid.UUID
    public_id: str
    old_card_version_id: uuid.UUID | None
    new_card_version_id: uuid.UUID | None
    card_kind: str | None = None
    note_type: str | None = None
    template_name: str | None = None
    # True when `fields` carry the original Anki field names (native upload),
    # so the client must NOT apply the legacy canonical field_mapping.
    native: bool = False
    content_hash: str | None = None
    fields: dict[str, str] | None = None
    template: dict[str, Any] | None = None
    source_note_id: str | None = None
    source_note_guid: str | None = None
    source_deck_path: str | None = None
    tags: list[str]


class AnkiDeckSyncResponse(BaseModel):
    deck_id: uuid.UUID
    from_release: int
    to_release: int
    has_changes: bool
    changes: list[AnkiSyncChangeResponse]
    page: int | None = None
    pages: int | None = None
    total_changes: int | None = None


class AnkiDeckStateCardResponse(BaseModel):
    card_id: uuid.UUID
    public_id: str
    card_version_id: uuid.UUID
    content_hash: str | None = None


class AnkiDeckStateResponse(BaseModel):
    deck_id: uuid.UUID
    latest_release: int
    total_active: int
    cards: list[AnkiDeckStateCardResponse]


class AnkiDeckReleaseSummaryResponse(BaseModel):
    release_id: uuid.UUID
    release_number: int
    published_at: datetime
    summary: str | None
    cards_added: int
    cards_updated: int
    cards_removed: int
    cards_deprecated: int


class AnkiDeckReleaseListResponse(BaseModel):
    deck_id: uuid.UUID
    latest_release: int
    items: list[AnkiDeckReleaseSummaryResponse]
    page: int
    page_size: int
    total: int
    pages: int


class AnkiDeckTemplateVersionResponse(BaseModel):
    template_id: uuid.UUID
    template_key: str
    template_name: str
    note_type: str
    card_kind: CardKind
    version_number: int
    content_hash: str
    status: str
    fields: list[str]
    field_mapping: dict[str, str]
    front_html: str
    back_html: str
    styling_css: str
    created_by: str
    created_at: datetime


class AnkiDeckTemplateSyncResponse(BaseModel):
    deck_id: uuid.UUID
    from_version: int
    to_version: int
    has_changes: bool
    changes: list[AnkiDeckTemplateVersionResponse]


class AnkiDeckTemplatePayload(BaseModel):
    template_name: str = Field(min_length=1, max_length=255)
    note_type: str = Field(min_length=1, max_length=255)
    card_kind: CardKind
    fields: list[str] = Field(min_length=1)
    field_mapping: dict[str, str] = Field(default_factory=dict)
    front_html: str = Field(min_length=1)
    back_html: str = Field(min_length=1)
    styling_css: str = Field(default="")

    @field_validator(
        "template_name",
        "note_type",
        "front_html",
        "back_html",
        mode="before",
    )
    @classmethod
    def strip_template_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AnkiDeckUploadNotePayload(BaseModel):
    note_type: str = Field(min_length=1, max_length=255)
    template_name: str | None = Field(default=None, max_length=255)
    card_kind: CardKind
    fields: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    source_note_id: str | None = Field(default=None, max_length=255)
    source_note_guid: str | None = Field(default=None, max_length=255)
    source_deck_path: str | None = Field(default=None, max_length=5000)

    @field_validator(
        "note_type",
        "template_name",
        "source_note_id",
        "source_note_guid",
        "source_deck_path",
        mode="before",
    )
    @classmethod
    def strip_note_type(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AnkiDeckUploadRequest(BaseModel):
    deck_name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    source_deck_path: str | None = Field(default=None, max_length=5000)
    source_name: str = Field(default="addon", min_length=1, max_length=100)
    publish_release: bool = True
    templates: list[AnkiDeckTemplatePayload] = Field(min_length=1)
    notes: list[AnkiDeckUploadNotePayload] = Field(min_length=1)

    @field_validator(
        "deck_name",
        "description",
        "source_deck_path",
        "source_name",
        mode="before",
    )
    @classmethod
    def strip_upload_metadata(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AnkiDeckUploadItemResponse(BaseModel):
    note_index: int
    status: Literal["created", "reused", "updated"]
    canonical_key: str
    card_id: uuid.UUID
    public_id: str
    card_version_id: uuid.UUID
    note_type: str
    card_kind: CardKind


class AnkiDeckUploadResponse(BaseModel):
    deck_id: uuid.UUID
    deck_name: str
    snapshot_id: uuid.UUID
    release_id: uuid.UUID | None
    latest_release: int
    published: bool
    total_notes: int
    created_cards: int
    reused_cards: int
    updated_cards: int = 0
    items: list[AnkiDeckUploadItemResponse]


class AddonStatusResponse(BaseModel):
    api_version: str
    min_addon_version: str
    supported_note_types: list[str]
