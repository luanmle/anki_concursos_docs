import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user
from app.models import User
from app.repositories import DeckRepository
from app.schemas import (
    DeckSubscriptionListResponse,
    DeckSubscriptionResponse,
    SubscribableDeckListResponse,
)
from app.services import DeckService

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)


def get_deck_service(
    session: Session = Depends(get_db, use_cache=False),
) -> DeckService:
    return DeckService(DeckRepository(session))


@router.get("/decks", response_model=SubscribableDeckListResponse)
def list_subscribable_decks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> SubscribableDeckListResponse:
    return service.list_subscribable_decks(
        user_id=user.id,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=DeckSubscriptionListResponse)
def list_subscriptions(
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> DeckSubscriptionListResponse:
    return service.list_subscriptions(user_id=user.id)


@router.post("/{deck_id}", response_model=DeckSubscriptionResponse)
def subscribe_to_deck(
    deck_id: uuid.UUID,
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> DeckSubscriptionResponse:
    return service.subscribe(deck_id, user_id=user.id)


@router.post("/{deck_id}/cancel", response_model=DeckSubscriptionResponse)
def cancel_deck_subscription(
    deck_id: uuid.UUID,
    user: User = Depends(require_authenticated_user),
    service: DeckService = Depends(get_deck_service),
) -> DeckSubscriptionResponse:
    return service.unsubscribe(deck_id, user_id=user.id)
