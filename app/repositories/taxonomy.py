import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Discipline, Topic


class TaxonomyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_disciplines(self) -> list[Discipline]:
        return list(
            self.session.scalars(
                select(Discipline).order_by(Discipline.name, Discipline.id)
            )
        )

    def get_discipline(self, discipline_id: uuid.UUID) -> Discipline | None:
        return self.session.get(Discipline, discipline_id)

    def list_topics(self, discipline_id: uuid.UUID) -> list[Topic]:
        return list(
            self.session.scalars(
                select(Topic)
                .where(Topic.discipline_id == discipline_id)
                .order_by(Topic.name, Topic.id)
            )
        )
