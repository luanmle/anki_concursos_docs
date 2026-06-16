import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import DeckStatus, ReleaseAction


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
    tags: list[str]


class AnkiCardFields(BaseModel):
    Front: str
    Back: str
    Answer: str
    Explanation: str


class AnkiSyncChangeResponse(BaseModel):
    release_id: uuid.UUID
    release_number: int
    published_at: datetime
    action: ReleaseAction
    card_id: uuid.UUID
    public_id: str
    old_card_version_id: uuid.UUID | None
    new_card_version_id: uuid.UUID | None
    fields: AnkiCardFields | None = None
    tags: list[str]


class AnkiDeckSyncResponse(BaseModel):
    deck_id: uuid.UUID
    from_release: int
    to_release: int
    has_changes: bool
    changes: list[AnkiSyncChangeResponse]
