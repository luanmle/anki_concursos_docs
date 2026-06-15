import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_staff
from app.repositories.taxonomy import TaxonomyRepository
from app.schemas.taxonomy import DisciplineListResponse, TopicListResponse
from app.services.taxonomy import TaxonomyService

router = APIRouter(
    prefix="/disciplines",
    tags=["taxonomy"],
    dependencies=[Depends(require_staff)],
)


def get_taxonomy_service(
    session: Session = Depends(get_db),
) -> TaxonomyService:
    return TaxonomyService(TaxonomyRepository(session))


@router.get("", response_model=DisciplineListResponse)
def list_disciplines(
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> DisciplineListResponse:
    return service.list_disciplines()


@router.get("/{discipline_id}/topics", response_model=TopicListResponse)
def list_topics(
    discipline_id: uuid.UUID,
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> TopicListResponse:
    return service.list_topics(discipline_id)
