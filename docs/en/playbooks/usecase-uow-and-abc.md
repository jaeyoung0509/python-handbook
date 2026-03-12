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

## How Session Injection Should Work in FastAPI

The most important wiring rule in the `ABC + UoW` pattern is this:

1. create the engine and `sessionmaker` once at process scope
2. let request-time dependencies provide a `sessionmaker` or `uow_factory`, not a live `Session`
3. let `SqlAlchemyUnitOfWork.__enter__()` and `__exit__()` own actual session creation and cleanup

The reason is ownership. If the UoW claims transaction ownership but FastAPI dependencies also open and close a separate live `Session`, the lifecycle becomes split and harder to reason about.

### 1. Create engine and sessionmaker in lifespan

```py
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> Iterator[None]:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    app.state.session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield
    finally:
        engine.dispose()
```

### 2. Let dependencies assemble the sessionmaker and use case

```py
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def get_register_user_use_case(
    session_factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    notifier: Annotated[AbstractWelcomeNotifier, Depends(get_notifier)],
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        notifier=notifier,
    )
```

### 3. Routes receive only the use case

```py
from typing import Annotated

from fastapi import APIRouter, Depends, status

router = APIRouter()


@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterUserRequest,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
) -> UserResponse:
    result = use_case.execute(
        RegisterUserCommand(email=payload.email, name=payload.name)
    )
    return UserResponse(id=result.id, email=result.email, name=result.name)
```

<p class="code-caption">The route should not know about session ownership directly. The dependency layer assembles `sessionmaker -> UoW factory -> use case`, and the UoW keeps transaction ownership coherent from start to finish.</p>

## How This Differs from Injecting a Live Session

### Inject a live Session when

- the service itself owns `with session.begin():`
- you are not using a separate UoW object
- session ownership is already obvious in the service layer

### Inject a sessionmaker or UoW factory when

- a class-based UoW owns session creation and cleanup
- the use case opens its transaction boundary with `with self.uow_factory() as uow:`
- several repositories should clearly share one transaction boundary

If you are using a UoW, injecting a sessionmaker or factory is usually cleaner than injecting a live Session.

## sub-optimal -> improved: when UoW ownership still stays blurry

### Bad example: the use case still owns session lifecycle and side-effect timing

```py
class RegisterUserUseCase:
    def __init__(self, session: Session, notifier: WelcomeNotifier) -> None:
        self.session = session
        self.notifier = notifier

    def execute(self, command: RegisterUserCommand) -> UserRead:
        repository = UserRepository(self.session)
        if repository.get_by_email(command.email) is not None:
            raise DuplicateEmail(command.email)

        record = UserModel(email=command.email, name=command.name)
        repository.add(record)
        self.session.commit()
        self.notifier.send(record.email, record.name)
        return UserRead(id=record.id, email=record.email, name=record.name)
```

<p class="code-caption">This looks simple, but the use case now knows session ownership, repository wiring, commit timing, and side-effect ordering. Once repositories grow or tests want to swap in fakes, those boundaries erode quickly.</p>

### Better example: the use case knows only abstract boundaries and the UoW owns the concrete lifecycle

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

<p class="code-caption">The improvement is not "more abstraction." The improvement is clearer ownership. The use case knows only transaction and side-effect boundaries, while the concrete UoW owns session creation, cleanup, and repository wiring.</p>

## Patterns to Avoid in This Wiring

- opening a live `Session` in `get_session()` while the UoW also creates another one internally
- reusing one singleton UoW instance across requests
- letting the use case receive `engine` or `Request` objects directly
- committing inside dependency wiring and leaking transaction policy out of the use case

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

## Code Review Lens

- Check whether the use case knows only transaction and external side-effect boundaries.
- Check whether the UoW owns session creation, cleanup, and repository wiring coherently.
- Check whether ABCs are used only where substitution and testing value are real.
- Check whether post-commit side-effect ordering is explicit and testable.

## Common Anti-Patterns

- giving the use case direct `Session`, `engine`, or `Request` objects and making it manage lifecycle details
- opening a live Session in dependencies while the UoW secretly opens another one
- abstracting helpers or DTOs that provide no substitution value
- firing notifiers or publishers before commit succeeds

## Likely Discussion Questions

- Why does injecting a `uow_factory` reveal ownership more clearly than injecting a live Session?
- Which boundaries deserve ABCs, and which should remain concrete?
- What should fake-UoW tests verify, and what still belongs to real DB integration tests?
- As repository count grows, what complexity does a UoW remove, and what does it not remove?

## Strong Answer Frame

- Start by defining the minimum boundaries the use case should know: transaction plus side effects.
- Explain how the current shape blurs session lifecycle, commit timing, and testability.
- Move concrete lifecycle concerns into the UoW and keep the use case dependent on small ABCs only.
- Close by separating the role of fake-UoW tests from real SQLAlchemy integration tests.

## Runnable Example in This Repository

This pattern is implemented in `examples/usecase_with_uow_abc.py`.

## Good Companion Chapters

- [Refactoring Atlas](/en/playbooks/refactoring-atlas)
- [Refactoring Session Ownership and Hidden Commits](/en/playbooks/refactoring-session-ownership-and-hidden-commits)
- [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
- [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)
- [ABC + Fake UoW Testing](/en/playbooks/testing-abc-and-fake-uow)
- [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)

## Official References

- [abc — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
