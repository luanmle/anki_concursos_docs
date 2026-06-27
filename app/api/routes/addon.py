import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models import User
from app.repositories import DeckRepository
from app.schemas import (
    AnkiDeckManifestResponse,
    AnkiDeckReleaseListResponse,
    AnkiDeckStateResponse,
    AnkiDeckSyncResponse,
    AnkiDeckTemplateSyncResponse,
)
from app.schemas.decks import (
    AddonStatusResponse,
    AnkiDeckUploadRequest,
    AnkiDeckUploadResponse,
)
from app.services import DeckService

router = APIRouter(prefix="/addon", tags=["addon"])


def get_deck_service(
    session: Session = Depends(get_db, use_cache=False),
) -> DeckService:
    return DeckService(DeckRepository(session))


@router.get("/status", response_model=AddonStatusResponse)
def get_addon_status() -> AddonStatusResponse:
    settings = get_settings()
    return AddonStatusResponse(
        api_version=settings.addon_api_version,
        min_addon_version=settings.min_addon_version,
        supported_note_types=[
            kind.value for kind in DeckService.ANKI_NOTE_TYPES.keys()
        ],
    )


@router.get("/decks/{deck_id}/manifest", response_model=AnkiDeckManifestResponse)
def get_anki_deck_manifest(
    deck_id: uuid.UUID,
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> AnkiDeckManifestResponse:
    return service.anki_manifest(deck_id, user_id=user.id)


@router.get("/decks/{deck_id}/sync", response_model=AnkiDeckSyncResponse)
def sync_anki_deck(
    deck_id: uuid.UUID,
    since_release: int = Query(default=0, ge=0),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=1000),
    to_release: int | None = Query(default=None, ge=0),
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
    ) -> AnkiDeckSyncResponse:
    return service.anki_sync(
        deck_id,
        user_id=user.id,
        since_release=since_release,
        page=page,
        page_size=page_size,
        to_release=to_release,
    )


@router.get("/decks/{deck_id}/state", response_model=AnkiDeckStateResponse)
def get_anki_deck_state(
    deck_id: uuid.UUID,
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> AnkiDeckStateResponse:
    return service.anki_deck_state(deck_id, user_id=user.id)


@router.get("/decks/{deck_id}/releases", response_model=AnkiDeckReleaseListResponse)
def list_anki_deck_releases(
    deck_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> AnkiDeckReleaseListResponse:
    return service.anki_releases(
        deck_id,
        user_id=user.id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/decks/{deck_id}/templates/sync",
    response_model=AnkiDeckTemplateSyncResponse,
)
def sync_anki_deck_templates(
    deck_id: uuid.UUID,
    since_version: int = Query(default=0, ge=0),
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> AnkiDeckTemplateSyncResponse:
    return service.anki_template_sync(
        deck_id,
        user_id=user.id,
        since_version=since_version,
    )


@router.post("/decks/upload", response_model=AnkiDeckUploadResponse, status_code=201)
def upload_anki_deck(
    payload: AnkiDeckUploadRequest,
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> AnkiDeckUploadResponse:
    return service.upload_anki_deck(payload, uploaded_by=user.email)
