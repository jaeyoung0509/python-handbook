# Use case + abc.ABC ports + SQLAlchemy Unit of Work.
# Use case + abc.ABC 기반 포트 + SQLAlchemy Unit of Work.
# Why: explicit abstract base classes make service boundaries visible at runtime and in code review.
# 왜: 명시적 추상 베이스 클래스는 서비스 경계를 런타임과 코드 리뷰에서 더 분명하게 보여준다.
# Use when: your team prefers concrete abstract classes over Protocol-based structural typing.
# 언제 쓰나: 팀이 Protocol 기반 구조적 타이핑보다 명시적 추상 클래스를 더 선호할 때 적합하다.

from __future__ import annotations

from abc import ABC, abstractmethod
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


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserRecord | None:
        raise NotImplementedError

    @abstractmethod
    def add(self, user: UserRecord) -> None:
        raise NotImplementedError


class AbstractUnitOfWork(ABC):
    @property
    @abstractmethod
    def users(self) -> AbstractUserRepository:
        raise NotImplementedError

    @abstractmethod
    def __enter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def flush(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class AbstractWelcomeNotifier(ABC):
    @abstractmethod
    def send(self, email: str, name: str) -> None:
        raise NotImplementedError


class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserRecord).where(UserRecord.email == email)
        return self.session.scalar(stmt)

    def add(self, user: UserRecord) -> None:
        self.session.add(user)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
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


class ConsoleWelcomeNotifier(AbstractWelcomeNotifier):
    def send(self, email: str, name: str) -> None:
        print(f"send welcome email -> {email} ({name})")


class RegisterUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractUnitOfWork],
        notifier: AbstractWelcomeNotifier,
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

        # Run side effects only after the transaction becomes durable.
        # 트랜잭션이 확정된 뒤에만 외부 부수효과를 실행한다.
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
