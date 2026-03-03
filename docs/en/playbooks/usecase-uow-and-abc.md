# Use Case + UoW + ABC

<p class="lead">This page is for teams that prefer `abc.ABC` over `Protocol` when translating SOLID ideas into Python service code. The goal is not to abstract every layer. The goal is to make the use case depend only on the boundaries that truly matter, while keeping SQLAlchemy implementation details outside.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: let the use case depend on small ABCs such as `AbstractUnitOfWork` and `AbstractNotifier`, while concrete SQLAlchemy session and repository wiring stays in a concrete UoW. Explicit abstract base classes make architectural boundaries easier to see in reviews and easier to fake in tests.</p>
</div>

## The Big Picture

<MermaidDiagram
  caption="The use case owns business rules, the UoW owns transaction boundaries, and side effects plus persistence stay behind separate abstract base classes."
  chart="flowchart LR; A[HTTP or CLI Input] --> B[RegisterUserUseCase]; B --> C[AbstractUnitOfWork]; C --> D[SqlAlchemyUnitOfWork]; D --> E[(Database)]; B --> F[AbstractWelcomeNotifier]; F --> G[Email or event implementation];"
/>

## Why Choose `abc.ABC`

### This style fits well when

- the team finds explicit class hierarchies easier to read than structural typing
- fake implementations should visibly match the production boundary
- architecture discussions and code reviews benefit from a runtime-visible contract

### That still does not mean "abstract everything"

- simple internal helpers
- concrete repositories that are unlikely to vary
- ORM entities, DTOs, or dataclass value objects

The useful rule is to abstract only the boundaries that provide real substitution or testing value.

## Recommended Structure

```py
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Self


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class UserRead:
    id: int
    email: str
    name: str


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserModel | None: ...

    @abstractmethod
    def add(self, user: UserModel) -> None: ...


class AbstractUnitOfWork(ABC):
    @property
    @abstractmethod
    def users(self) -> AbstractUserRepository: ...

    @abstractmethod
    def __enter__(self) -> Self: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    def flush(self) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


class AbstractWelcomeNotifier(ABC):
    @abstractmethod
    def send(self, email: str, name: str) -> None: ...
```

<p class="code-caption">The important point is that the use case does not know about sessions, engines, or ORM lifecycle details. It knows only the transaction boundary and the external side-effect boundary.</p>

## The Use Case Depends Only on Abstract Boundaries

```py
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

            record = UserModel(email=command.email, name=command.name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()

        self.notifier.send(result.email, result.name)
        return result
```

## Keep Concrete SQLAlchemy Code Outside

```py
from sqlalchemy.orm import Session, sessionmaker


class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session


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

    def __exit__(self, exc_type, exc, tb) -> None:
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
```

## Testing Gets Easier With a Fake UoW

```py
class FakeUserRepository(AbstractUserRepository):
    def __init__(self) -> None:
        self.items: dict[str, UserModel] = {}

    def get_by_email(self, email: str) -> UserModel | None:
        return self.items.get(email)

    def add(self, user: UserModel) -> None:
        self.items[user.email] = user


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self._users = FakeUserRepository()
        self.committed = False

    @property
    def users(self) -> FakeUserRepository:
        return self._users

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.rollback()

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = False
```

<p class="code-caption">A fake UoW makes it easy to test rules such as "do not commit on duplicate email" or "send one notification after a successful commit" without opening a real database connection.</p>

## Patterns to Avoid

- turning repositories, services, use cases, and DTOs all into ABCs
- hiding every query shape behind one generic repository
- letting the UoW know about FastAPI dependencies, HTTP status codes, or response DTOs
- triggering emails or event publishes before commit
- reusing one UoW instance like a singleton

## Runnable Example in This Repository

This pattern is implemented in `examples/usecase_with_uow_abc.py`.

## Good Companion Chapters

- [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
- [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)
- [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)

## Official References

- [abc — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
