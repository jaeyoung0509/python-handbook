# Use Case + UoW + Interface

<p class="lead">This page shows how to translate "SOLID-aware design" into practical Python service code. The point is not to wrap everything in interfaces. The point is to abstract only the boundaries a use case truly depends on, while leaving infrastructure such as SQLAlchemy UoW implementations concrete.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: let use cases depend on small `Protocol`-based ports, while keeping SQLAlchemy Unit of Work implementations concrete. DIP does not mean "turn every class into an interface." It means placing abstractions only where substitution and testing actually matter.</p>
</div>

## The Big Picture

<MermaidDiagram
  caption="The use case composes a transaction boundary with external side-effect boundaries. The UoW owns database work; side effects such as notifications stay behind separate ports."
  chart="flowchart LR; A[HTTP or CLI Input] --> B[Use Case]; B --> C[UnitOfWork Protocol]; C --> D[SqlAlchemyUnitOfWork]; D --> E[(Database)]; B --> F[Notifier Protocol]; F --> G[Email or event implementation];"
/>

## Which Boundaries Deserve Interfaces?

### Usually worth abstracting

- external side effects such as email, queue publishing, or payment gateways
- the unit-of-work boundary the use case directly coordinates
- ports you genuinely want to fake in tests

### Often not worth abstracting

- simple internal CRUD helpers
- concrete repositories that are unlikely to vary meaningfully
- SQLAlchemy models themselves

## Recommended Structure

```py
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class UserRead:
    id: int
    email: str
    name: str


class UserRepositoryPort(Protocol):
    def get_by_email(self, email: str) -> UserModel | None: ...
    def add(self, user: UserModel) -> None: ...


class UnitOfWorkPort(Protocol):
    users: UserRepositoryPort

    def __enter__(self) -> "UnitOfWorkPort": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class WelcomeNotifier(Protocol):
    def send(self, email: str, name: str) -> None: ...
```

## The Use Case Depends Only on Ports

```py
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

            record = UserModel(email=command.email, name=command.name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()

        self.notifier.send(result.email, result.name)
        return result
```

<p class="code-caption">The important point is that external side effects happen after commit. Sending an email or publishing an event before the transaction is durable can leave the outside world ahead of the database.</p>

## A Concrete SQLAlchemy Implementation

```py
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self.users: SqlAlchemyUserRepository | None = None

    def __enter__(self) -> Self:
        session = self.session_factory()
        self.session = session
        self.users = SqlAlchemyUserRepository(session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None and self.session is not None:
            self.session.rollback()
        if self.session is not None:
            self.session.close()

    def flush(self) -> None:
        assert self.session is not None
        self.session.flush()

    def commit(self) -> None:
        assert self.session is not None
        self.session.commit()

    def rollback(self) -> None:
        assert self.session is not None
        self.session.rollback()
```

## Why This Pattern Ages Well

- the use case is not directly tied to SQLAlchemy details
- the UoW groups transaction ownership with repository wiring
- side effects such as notifications are easy to fake in tests
- the abstractions stay small and meaningful

## Patterns to Avoid

- turning repositories, services, use cases, and DTOs all into interfaces
- hiding every query shape behind one generic repository
- letting the UoW know about HTTP status codes or FastAPI dependencies
- triggering external side effects before commit
- creating ports that have no real substitution value

## Runnable Example in This Repository

This pattern is implemented as a runnable example in `examples/usecase_with_uow_interfaces.py`.

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Use cases depend on ports</h3>
    <p>Database and side-effect details should stay outside the use case.</p>
  </div>
  <div class="check-card">
    <h3>UoW owns transactions</h3>
    <p>Session creation, repository wiring, rollback, and close belong together.</p>
  </div>
  <div class="check-card">
    <h3>Commit before side effects</h3>
    <p>Emails and events should usually happen after the database change is durable.</p>
  </div>
  <div class="check-card">
    <h3>Abstract only where needed</h3>
    <p>DIP is a tool for meaningful boundaries, not a rule that every layer needs an interface.</p>
  </div>
</div>

## Official References

- [Python typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
