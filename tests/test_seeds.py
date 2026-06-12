from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Discipline, Topic
from app.seeds.taxonomy import INITIAL_TAXONOMY, seed_taxonomy


def test_taxonomy_seed_is_idempotent(session: Session) -> None:
    seed_taxonomy(session)
    seed_taxonomy(session)

    assert session.scalar(select(func.count()).select_from(Discipline)) == len(INITIAL_TAXONOMY)
    assert session.scalar(select(func.count()).select_from(Topic)) == sum(
        len(topics) for topics in INITIAL_TAXONOMY.values()
    )

