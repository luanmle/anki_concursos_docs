from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Discipline, Topic

INITIAL_TAXONOMY = {
    "Direito Constitucional": [
        "Direitos e garantias fundamentais",
        "Organização do Estado",
        "Poderes da República",
    ],
    "Direito Administrativo": [
        "Atos administrativos",
        "Licitações e contratos",
        "Agentes públicos",
    ],
    "Língua Portuguesa": [
        "Interpretação de textos",
        "Morfologia",
        "Sintaxe",
    ],
    "Raciocínio Lógico": [
        "Lógica proposicional",
        "Conjuntos",
        "Probabilidade",
    ],
    "Informatica": [
        "Sistemas operacionais",
        "Redes de computadores",
        "Segurança da informação",
    ],
}


def seed_taxonomy(session: Session) -> None:
    for discipline_name, topic_names in INITIAL_TAXONOMY.items():
        discipline = session.scalar(
            select(Discipline).where(Discipline.name == discipline_name)
        )
        if discipline is None:
            discipline = Discipline(name=discipline_name)
            session.add(discipline)
            session.flush()

        existing_topics = set(
            session.scalars(
                select(Topic.name).where(Topic.discipline_id == discipline.id)
            )
        )
        session.add_all(
            Topic(discipline_id=discipline.id, name=topic_name)
            for topic_name in topic_names
            if topic_name not in existing_topics
        )

    session.commit()


def main() -> None:
    with SessionLocal() as session:
        seed_taxonomy(session)


if __name__ == "__main__":
    main()
