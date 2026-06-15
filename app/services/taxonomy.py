import uuid

from fastapi import HTTPException, status

from app.models import Discipline, Topic
from app.repositories.taxonomy import TaxonomyRepository
from app.schemas.taxonomy import (
    DisciplineListResponse,
    DisciplineResponse,
    TopicListResponse,
    TopicResponse,
)


class TaxonomyService:
    def __init__(self, repository: TaxonomyRepository) -> None:
        self.repository = repository

    def list_disciplines(self) -> DisciplineListResponse:
        disciplines = self.repository.list_disciplines()
        return DisciplineListResponse(
            items=[self._discipline_response(item) for item in disciplines],
            total=len(disciplines),
        )

    def list_topics(self, discipline_id: uuid.UUID) -> TopicListResponse:
        discipline = self.repository.get_discipline(discipline_id)
        if discipline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discipline not found",
            )
        topics = self.repository.list_topics(discipline_id)
        return TopicListResponse(
            discipline=self._discipline_response(discipline),
            items=[self._topic_response(item) for item in topics],
            total=len(topics),
        )

    @staticmethod
    def _discipline_response(discipline: Discipline) -> DisciplineResponse:
        return DisciplineResponse(
            discipline_id=discipline.id,
            name=discipline.name,
            parent_id=discipline.parent_id,
        )

    @staticmethod
    def _topic_response(topic: Topic) -> TopicResponse:
        return TopicResponse(
            topic_id=topic.id,
            discipline_id=topic.discipline_id,
            name=topic.name,
            parent_id=topic.parent_id,
        )
