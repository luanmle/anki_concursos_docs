from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Card,
    CardVersion,
    Deck,
    DeckCard,
    NoteSuggestion,
    NoteSuggestionComment,
)
from app.models.enums import CardStatus, DeckStatus, NoteSuggestionStatus


class NoteSuggestionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_published_card(self, card_id: uuid.UUID) -> Card | None:
        return self.session.scalar(
            select(Card)
            .options(joinedload(Card.current_version))
            .where(Card.id == card_id, Card.status == CardStatus.PUBLISHED)
        )

    def get_published_deck(self, deck_id: uuid.UUID) -> Deck | None:
        return self.session.scalar(
            select(Deck).where(Deck.id == deck_id, Deck.status == DeckStatus.PUBLISHED)
        )

    def create(self, suggestion: NoteSuggestion) -> NoteSuggestion:
        self.session.add(suggestion)
        self.session.flush()
        return suggestion

    def get(
        self,
        suggestion_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> NoteSuggestion | None:
        statement = (
            select(NoteSuggestion)
            .options(
                joinedload(NoteSuggestion.card),
                joinedload(NoteSuggestion.card_version),
            )
            .where(NoteSuggestion.id == suggestion_id)
        )
        if for_update:
            statement = statement.with_for_update(of=NoteSuggestion)
        return self.session.scalar(statement)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        status: NoteSuggestionStatus | None,
    ) -> tuple[list[NoteSuggestion], int]:
        filters = []
        if status is not None:
            filters.append(NoteSuggestion.status == status)

        total = self.session.scalar(
            select(func.count()).select_from(NoteSuggestion).where(*filters)
        ) or 0
        statement = (
            select(NoteSuggestion)
            .options(
                joinedload(NoteSuggestion.card),
                joinedload(NoteSuggestion.card_version),
            )
            .where(*filters)
            .order_by(NoteSuggestion.created_at.desc(), NoteSuggestion.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def get_deck(self, deck_id: uuid.UUID) -> Deck | None:
        return self.session.get(Deck, deck_id)

    def list_for_deck(
        self,
        deck_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        status: NoteSuggestionStatus | None,
    ) -> tuple[list[NoteSuggestion], int]:
        # ponytail: card pertence ao deck via qualquer linha em deck_cards
        # (inclui cards removidos — sugestao historica continua visivel).
        deck_card_ids = select(DeckCard.card_id).where(DeckCard.deck_id == deck_id)
        scope = (NoteSuggestion.deck_id == deck_id) | (
            NoteSuggestion.card_id.in_(deck_card_ids)
        )
        filters = [scope]
        if status is not None:
            filters.append(NoteSuggestion.status == status)

        total = self.session.scalar(
            select(func.count()).select_from(NoteSuggestion).where(*filters)
        ) or 0
        statement = (
            select(NoteSuggestion)
            .options(
                joinedload(NoteSuggestion.card),
                joinedload(NoteSuggestion.card_version),
            )
            .where(*filters)
            .order_by(NoteSuggestion.created_at.desc(), NoteSuggestion.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def list_comments(
        self, suggestion_id: uuid.UUID
    ) -> list[NoteSuggestionComment]:
        statement = (
            select(NoteSuggestionComment)
            .where(NoteSuggestionComment.suggestion_id == suggestion_id)
            .order_by(NoteSuggestionComment.created_at, NoteSuggestionComment.id)
        )
        return list(self.session.scalars(statement))

    def create_comment(
        self, comment: NoteSuggestionComment
    ) -> NoteSuggestionComment:
        self.session.add(comment)
        self.session.flush()
        return comment

    def next_card_version_number(self, card_id: uuid.UUID) -> int:
        current = self.session.scalar(
            select(func.max(CardVersion.version_number)).where(
                CardVersion.card_id == card_id
            )
        )
        return (current or 0) + 1

    def card_version_hashes(self, card_id: uuid.UUID) -> set[str]:
        return set(
            self.session.scalars(
                select(CardVersion.content_hash).where(
                    CardVersion.card_id == card_id
                )
            )
        )

    def add_card_version(self, version: CardVersion) -> CardVersion:
        self.session.add(version)
        self.session.flush()
        return version
