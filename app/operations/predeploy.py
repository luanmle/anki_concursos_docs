import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.honeybadger import configure_honeybadger, notify_exception
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models import User
from app.models.enums import UserRole
from app.seeds.taxonomy import seed_taxonomy

logger = logging.getLogger("app.predeploy")
MIGRATION_LOCK_ID = 731_240_612


def run_migrations() -> None:
    config = Config("alembic.ini")
    if engine.dialect.name != "postgresql":
        command.upgrade(config, "head")
        return
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "SELECT pg_advisory_lock(%s)",
            (MIGRATION_LOCK_ID,),
        )
        try:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        finally:
            connection.exec_driver_sql(
                "SELECT pg_advisory_unlock(%s)",
                (MIGRATION_LOCK_ID,),
            )


def bootstrap_admin() -> None:
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        logger.info("bootstrap_admin_skipped")
        return
    email = settings.bootstrap_admin_email.strip().lower()
    with SessionLocal() as session:
        existing = session.scalar(select(User).where(User.email == email))
        if existing is not None:
            logger.info("bootstrap_admin_exists")
            return
        session.add(
            User(
                email=email,
                display_name=settings.bootstrap_admin_name.strip(),
                password_hash=hash_password(settings.bootstrap_admin_password),
                role=UserRole.ADMIN,
            )
        )
        session.commit()
        logger.info("bootstrap_admin_created")


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_honeybadger(settings)
    try:
        run_migrations()
        with SessionLocal() as session:
            seed_taxonomy(session)
        bootstrap_admin()
        logger.info("predeploy_completed")
    except Exception as exc:
        notify_exception(
            exc,
            context={"operation": "predeploy"},
            tags=["deploy", "predeploy"],
        )
        raise


if __name__ == "__main__":
    main()
