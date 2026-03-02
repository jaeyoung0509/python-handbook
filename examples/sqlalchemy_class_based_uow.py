# Class-based SQLAlchemy Unit of Work: one session, grouped repositories, explicit commit.
# 클래스 기반 SQLAlchemy Unit of Work: 하나의 session, 묶인 repository, 명시적 commit.
# Why: once multiple repositories share one business transaction, an explicit UoW object can make ownership clearer.
# 왜: 여러 repository가 하나의 비즈니스 트랜잭션을 공유하기 시작하면 명시적 UoW 객체가 소유권을 더 잘 드러낸다.
# Use when: you want service methods to depend on "one unit of work" rather than a raw SQLAlchemy session.
# 언제 쓰나: service가 raw session보다 "하나의 작업 단위"에 의존하게 만들고 싶을 때 좋다.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Self

from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))


@dataclass(slots=True, frozen=True)
class UserRead:
    id: int
    email: str
    name: str


class DuplicateEmail(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(email)


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserRecord).where(UserRecord.email == email)
        return self.session.scalar(stmt)

    def add(self, record: UserRecord) -> None:
        self.session.add(record)

    def list_all(self) -> list[UserRecord]:
        stmt = select(UserRecord).order_by(UserRecord.id)
        return list(self.session.scalars(stmt))


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._users: UserRepository | None = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        return self._session

    @property
    def users(self) -> UserRepository:
        if self._users is None:
            raise RuntimeError("unit of work not entered")
        return self._users

    def __enter__(self) -> Self:
        session = self._session_factory()
        self._session = session
        self._users = UserRepository(session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None and self._session is not None:
            self._session.rollback()
        if self._session is not None:
            self._session.close()

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


class RegisterUserService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self.uow_factory = uow_factory

    def execute(self, email: str, name: str) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(email) is not None:
                raise DuplicateEmail(email)

            record = UserRecord(email=email, name=name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()
            return result


def main() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )

    service = RegisterUserService(lambda: SqlAlchemyUnitOfWork(session_factory))
    print("create 1:", service.execute("neo@example.com", "Neo"))
    print("create 2:", service.execute("trinity@example.com", "Trinity"))

    try:
        service.execute("neo@example.com", "Duplicate Neo")
    except DuplicateEmail as exc:
        print("duplicate:", exc.email)

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        print(
            "stored users:",
            [UserRead(id=row.id, email=row.email, name=row.name) for row in uow.users.list_all()],
        )


if __name__ == "__main__":
    main()
