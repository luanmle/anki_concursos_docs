import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(
        self,
        user_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> User | None:
        statement = select(User).where(User.id == user_id)
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def list_users(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[User], int]:
        total = self.session.scalar(select(func.count()).select_from(User)) or 0
        statement = (
            select(User)
            .order_by(User.email, User.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def lock_active_admins(self) -> list[User]:
        from app.models.enums import UserRole

        return list(
            self.session.scalars(
                select(User)
                .where(
                    User.role == UserRole.ADMIN,
                    User.is_active.is_(True),
                )
                .order_by(User.id)
                .with_for_update()
            )
        )

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
