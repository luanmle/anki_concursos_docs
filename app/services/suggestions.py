import math
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models import NoteSuggestion, NoteSuggestionComment, User
from app.models.enums import NoteSuggestionStatus
from app.repositories import NoteSuggestionRepository
from app.schemas import (
    NoteSuggestionCommentCreateRequest,
    NoteSuggestionCommentListResponse,
    NoteSuggestionCommentResponse,
    NoteSuggestionCreateRequest,
    NoteSuggestionListResponse,
    NoteSuggestionResponse,
    NoteSuggestionReviewRequest,
)


class NoteSuggestionService:
    def __init__(self, repository: NoteSuggestionRepository) -> None:
        self.repository = repository
        self.session = repository.session

    def create_for_card(
        self,
        card_id: uuid.UUID,
        payload: NoteSuggestionCreateRequest,
        user: User,
    ) -> NoteSuggestionResponse:
        try:
            card = self.repository.get_published_card(card_id)
            if card is None or card.current_version is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Published card not found",
                )
            suggestion = self.repository.create(
                NoteSuggestion(
                    card_id=card.id,
                    card_version_id=card.current_version.id,
                    submitted_by_user_id=user.id,
                    submitted_by_email=user.email,
                    suggestion_type=payload.suggestion_type,
                    fields=payload.fields,
                    added_tags=payload.added_tags,
                    removed_tags=payload.removed_tags,
                    comment=payload.comment,
                    source=payload.source,
                )
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suggestion could not be created",
            ) from exc
        return self.get(suggestion.id)

    def create_for_deck(
        self,
        deck_id: uuid.UUID,
        payload: NoteSuggestionCreateRequest,
        user: User,
    ) -> NoteSuggestionResponse:
        try:
            if self.repository.get_published_deck(deck_id) is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Published deck not found",
                )
            suggestion = self.repository.create(
                NoteSuggestion(
                    deck_id=deck_id,
                    submitted_by_user_id=user.id,
                    submitted_by_email=user.email,
                    suggestion_type=payload.suggestion_type,
                    fields=payload.fields,
                    added_tags=payload.added_tags,
                    removed_tags=payload.removed_tags,
                    comment=payload.comment,
                    source=payload.source,
                )
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suggestion could not be created",
            ) from exc
        return self.get(suggestion.id)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        status_filter: NoteSuggestionStatus | None,
    ) -> NoteSuggestionListResponse:
        suggestions, total = self.repository.list(
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        return NoteSuggestionListResponse(
            items=[self._response(item) for item in suggestions],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def get(self, suggestion_id: uuid.UUID) -> NoteSuggestionResponse:
        suggestion = self.repository.get(suggestion_id)
        if suggestion is None:
            self._raise_not_found()
        return self._response(suggestion)

    def list_for_deck(
        self,
        deck_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        status_filter: NoteSuggestionStatus | None,
    ) -> NoteSuggestionListResponse:
        if self.repository.get_deck(deck_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found",
            )
        suggestions, total = self.repository.list_for_deck(
            deck_id,
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        return NoteSuggestionListResponse(
            items=[self._response(item) for item in suggestions],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def list_comments(
        self, suggestion_id: uuid.UUID
    ) -> NoteSuggestionCommentListResponse:
        if self.repository.get(suggestion_id) is None:
            self._raise_not_found()
        comments = self.repository.list_comments(suggestion_id)
        return NoteSuggestionCommentListResponse(
            items=[self._comment_response(item) for item in comments],
            total=len(comments),
        )

    def add_comment(
        self,
        suggestion_id: uuid.UUID,
        payload: NoteSuggestionCommentCreateRequest,
        user: User,
    ) -> NoteSuggestionCommentResponse:
        if self.repository.get(suggestion_id) is None:
            self._raise_not_found()
        comment = self.repository.create_comment(
            NoteSuggestionComment(
                suggestion_id=suggestion_id,
                author_user_id=user.id,
                author_email=user.email,
                body=payload.body,
            )
        )
        self.session.commit()
        return self._comment_response(comment)

    def review(
        self,
        suggestion_id: uuid.UUID,
        payload: NoteSuggestionReviewRequest,
        *,
        reviewed_by: str,
    ) -> NoteSuggestionResponse:
        try:
            suggestion = self.repository.get(suggestion_id, for_update=True)
            if suggestion is None:
                self._raise_not_found()
            if suggestion.status != NoteSuggestionStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Suggestion has already been reviewed",
                )
            suggestion.status = payload.status
            suggestion.reviewed_by = reviewed_by
            suggestion.review_comment = payload.review_comment
            suggestion.resulting_card_version_id = payload.resulting_card_version_id
            suggestion.reviewed_at = datetime.now(UTC)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Suggestion review could not be completed",
            ) from exc
        return self.get(suggestion_id)

    @staticmethod
    def _response(suggestion: NoteSuggestion) -> NoteSuggestionResponse:
        version = suggestion.card_version
        return NoteSuggestionResponse(
            suggestion_id=suggestion.id,
            deck_id=suggestion.deck_id,
            card_id=suggestion.card_id,
            public_id=suggestion.card.public_id if suggestion.card else None,
            card_version_id=suggestion.card_version_id,
            version_number=version.version_number if version else None,
            submitted_by_user_id=suggestion.submitted_by_user_id,
            submitted_by_email=suggestion.submitted_by_email,
            suggestion_type=suggestion.suggestion_type,
            status=suggestion.status,
            fields=suggestion.fields,
            added_tags=suggestion.added_tags,
            removed_tags=suggestion.removed_tags,
            comment=suggestion.comment,
            source=suggestion.source,
            reviewed_by=suggestion.reviewed_by,
            review_comment=suggestion.review_comment,
            reviewed_at=NoteSuggestionService._as_utc(suggestion.reviewed_at),
            resulting_card_version_id=suggestion.resulting_card_version_id,
            created_at=NoteSuggestionService._as_utc(suggestion.created_at),
            updated_at=NoteSuggestionService._as_utc(suggestion.updated_at),
        )

    @staticmethod
    def _comment_response(
        comment: NoteSuggestionComment,
    ) -> NoteSuggestionCommentResponse:
        return NoteSuggestionCommentResponse(
            comment_id=comment.id,
            suggestion_id=comment.suggestion_id,
            author_user_id=comment.author_user_id,
            author_email=comment.author_email,
            body=comment.body,
            created_at=NoteSuggestionService._as_utc(comment.created_at),
        )

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _raise_not_found() -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found",
        )
