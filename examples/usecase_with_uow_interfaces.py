# Use case + Protocol interfaces + SQLAlchemy Unit of Work.
# Use case + Protocol 인터페이스 + SQLAlchemy Unit of Work.
# Why: dependency inversion is most useful at real boundaries such as unit of work ownership and external side effects.
# 왜: DIP는 unit of work 경계와 외부 부수효과 같은 "진짜 경계"에서 가장 가치가 크다.
# Use when: designing use cases that should stay testable without abstracting every internal class.
# 언제 쓰나: 내부 모든 클래스를 인터페이스화하지 않으면서 use case를 테스트 가능하게 유지하고 싶을 때 좋다.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self

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


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class UserRead:
    id: int
    email: str
    name: str


class DuplicateEmail(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(email)


class UserRepositoryPort(Protocol):
    def get_by_email(self, email: str) -> UserRecord | None: ...
    def add(self, user: UserRecord) -> None: ...


class UnitOfWorkPort(Protocol):
    users: UserRepositoryPort

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class WelcomeNotifier(Protocol):
    def send(self, email: str, name: str) -> None: ...


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserRecord).where(UserRecord.email == email)
        return self.session.scalar(stmt)

    def add(self, user: UserRecord) -> None:
        self.session.add(user)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._users: SqlAlchemyUserRepository | None = None

    @property
    def users(self) -> SqlAlchemyUserRepository:
        if self._users is None:
            raise RuntimeError("unit of work not entered")
        return self._users

    def __enter__(self) -> Self:
        session = self._session_factory()
        self._session = session
        self._users = SqlAlchemyUserRepository(session)
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
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        self._session.flush()

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        self._session.commit()

    def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        self._session.rollback()


class ConsoleWelcomeNotifier:
    def send(self, email: str, name: str) -> None:
        print(f"send welcome email -> {email} ({name})")


class RegisterUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWorkPort],
        notifier: WelcomeNotifier,
    ) -> None:
        self.uow_factory = uow_factory
        self.notifier = notifier

    def execute(self, command: RegisterUserCommand) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(command.email) is not None:
                raise DuplicateEmail(command.email)

            record = UserRecord(email=command.email, name=command.name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()

        # External side effects are safer after commit.
        # 외부 부수효과는 commit 뒤로 미루는 편이 더 안전하다.
        self.notifier.send(result.email, result.name)
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

    use_case = RegisterUserUseCase(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        notifier=ConsoleWelcomeNotifier(),
    )

    created = use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))
    print("created:", created)

    try:
        use_case.execute(RegisterUserCommand(email="neo@example.com", name="Another Neo"))
    except DuplicateEmail as exc:
        print("duplicate:", exc.email)


if __name__ == "__main__":
    main()
