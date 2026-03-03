# Session and Unit of Work

<p class="lead">A large share of SQLAlchemy bugs come from the wrong mental model of `Session`. Once it is treated like a global cache, a connection handle, or a repository replacement, transaction boundaries, stale state, lazy loading, and tests all start to drift.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a session is a short-lived work context that owns an identity map and a unit of work. Repositories use the session, but commits and rollbacks belong at the use-case boundary.</p>
</div>

## Start With the Lifecycle Picture

<MermaidDiagram
  caption="The stable shape is one request or one use case owning one session, with repository work and flushes happening inside that scope before a final commit or rollback."
  chart="flowchart LR; A[HTTP Request or Use Case] --> B[Session Scope]; B --> C[Repository Calls]; C --> D[Pending ORM State]; D --> E[flush]; E --> F[commit or rollback]; F --> G[Session Close];"
/>

## Four Wrong Mental Models

| Wrong model | What it actually is | Why it hurts |
| --- | --- | --- |
| The session is a global cache | It is a scoped identity map | Long-lived scope creates stale state and memory problems |
| The session is just a connection | It borrows connections as needed for transaction work | You end up confusing pool lifetime with session lifetime |
| Every repository can own its own session | One use case should usually share one session and transaction | Commits get fragmented inside a single business action |
| Repositories can commit safely | Commit belongs to the use-case boundary | Atomic multi-step workflows become hard to reason about |

## Baseline Session Lifetime Pattern

```py
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "postgresql+psycopg://app:secret@localhost/app"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Iterator[Session]:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
```

<p class="code-caption">`sessionmaker` creates fresh sessions. The session is closed when the request or work unit ends. Avoid storing a live session as a module-level singleton. In API code, `expire_on_commit=False` is a common choice because response DTO assembly and logging after commit become less surprising.</p>

## `sessionmaker()` Defaults Are Part of the Design

| Setting | Common default | Why teams often pick it | Watch out for |
| --- | --- | --- | --- |
| `autoflush=False` | often enabled | reduces hidden SQL during reads and boundary code | you must call `flush()` deliberately |
| `expire_on_commit=False` | often enabled in APIs | post-commit access becomes more predictable | it does not justify long-lived sessions |
| `class_=Session` | often explicit | keeps sync/async factory intent readable | async code must use `AsyncSession` equivalents |

<p class="code-caption">These are not universal truths, but they are practical defaults for service code. Web APIs often want explicit flush/commit timing and predictable access right after commit. Engine and pool settings depend on the deployment model, so treat them separately in [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings).</p>

## Know the Session API by Behavior

| API | Meaning | Use it for | Common trap |
| --- | --- | --- | --- |
| `add(obj)` | Stage an object in the unit of work | New ORM instances | Thinking `add()` immediately runs `INSERT` |
| `flush()` | Synchronize pending state with the DB | Need generated PKs or early constraint feedback | Confusing flush with transaction completion |
| `commit()` | Finalize the current transaction | End of a successful use case | Calling it inside repository helpers |
| `rollback()` | Cancel the current transaction | Failure recovery | Ignoring object state after rollback |
| `refresh(obj)` | Reload attributes from the DB | Need server-side defaults or trigger results | Calling it after every write by habit |
| `get(Model, pk)` | PK lookup with identity-map awareness | Single-entity load by primary key | Trying to use it for arbitrary filters |
| `execute(stmt)` | General statement execution | Core or ORM statements | Treating it as the only ORM API |
| `scalars(stmt)` | Scalar or ORM-object result stream | ORM `select()` results | Missing the difference from raw rows |
| `delete(obj)` | Mark entity for deletion | Delete use cases | Thinking it always issues SQL immediately |
| `begin()` | Transaction context manager | Clear write boundaries | Confusing session scope with transaction scope |
| `begin_nested()` | SAVEPOINT context | Tests or partial rollback | Using it as a default request pattern |
| `close()` | End the session scope | Request end, job end | Treating close as equivalent to commit |

## Why `flush()` and `commit()` Must Stay Separate

```py
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        return self.session.scalar(stmt)

    def add(self, user: UserModel) -> None:
        self.session.add(user)


class RegisterUserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def execute(self, email: str, name: str) -> UserRead:
        with self.session.begin():
            if self.users.get_by_email(email) is not None:
                raise DuplicateEmail(email)

            record = UserModel(email=email, name=name)
            self.users.add(record)

            self.session.flush()

            return UserRead(
                id=record.id,
                email=record.email,
                name=record.name,
            )
```

<p class="code-caption">`flush()` sends SQL so you can get generated values like primary keys. The transaction is still open. The final commit happens when the `with self.session.begin():` block exits successfully.</p>

## Good Design Moves Commit to the Right Place

### Recommended

- Start the transaction at the service or use-case boundary.
- Keep repositories focused on loading and staging ORM entities.
- Let multiple repository operations share the same session inside one business action.

### Avoid

- Calling `commit()` in repository methods.
- Creating a new session inside every helper function.
- Returning ORM entities straight through the API boundary.

## Identity Map Is Not a General Query Cache

- Within one session, the same primary-key row is usually represented by the same Python object.
- That does not mean all queries are cached.
- Queries with arbitrary filters can still emit SQL even if matching entities already exist in the identity map.
- Keep session scope short; long-lived sessions rarely pay off.

## The Safest FastAPI Pattern

```py
from fastapi import Depends
from sqlalchemy.orm import Session


def get_user_service(session: Session = Depends(get_session)) -> RegisterUserService:
    return RegisterUserService(session)
```

- One request gets one session.
- The same session flows into all repositories used by that request.
- The dependency closes the session when the request finishes.

## An `abc.ABC`-Based Class Unit of Work Pattern

Passing the session directly into a service is already a solid default. But once repository groups grow and you want transaction ownership to read as one explicit object, a class-based Unit of Work can make the design easier to scan.

```py
from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker


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


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self._users: SqlAlchemyUserRepository | None = None

    @property
    def users(self) -> SqlAlchemyUserRepository:
        if self._users is None:
            raise RuntimeError("unit of work not entered")
        return self._users

    def __enter__(self) -> Self:
        session = self.session_factory()
        self.session = session
        self._users = SqlAlchemyUserRepository(session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.session is not None:
            if exc is not None:
                self.session.rollback()
            self.session.close()

    def flush(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work not entered")
        self.session.flush()

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work not entered")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work not entered")
        self.session.rollback()


class RegisterUserService:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractUnitOfWork],
    ) -> None:
        self.uow_factory = uow_factory

    def execute(self, email: str, name: str) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(email) is not None:
                raise DuplicateEmail(email)

            record = UserModel(email=email, name=name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()
            return result
```

<p class="code-caption">The Unit of Work owns the session plus the repository set. The service decides when to commit, while session creation, repository wiring, and cleanup stay inside one object. If your team prefers explicit runtime contracts over structural typing, this style is often easier to scan in reviews. This repository now includes a runnable example of the same pattern in `examples/usecase_with_uow_abc.py`.</p>

## When a Class-Based UoW Fits Well

- when several repositories should always share one transaction
- when you want service signatures to express "one unit of work" rather than "a raw session"
- when your team prefers explicit `abc.ABC` contracts over structural typing
- when tests benefit from swapping in a fake UoW for use-case branching

## Patterns to Avoid with a Class-Based UoW

- repositories inside the UoW committing independently
- reusing one UoW instance like a long-lived singleton
- accessing repository or session attributes before `__enter__()`
- letting the UoW know about HTTP status codes or response DTO creation

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>One request, one session</h3>
    <p>In web services, request scope is the default. Background jobs and workers should own their own sessions.</p>
  </div>
  <div class="check-card">
    <h3>One use case, one commit</h3>
    <p>Make the transaction boundary line up with one business action.</p>
  </div>
  <div class="check-card">
    <h3>Return DTOs, not entities</h3>
    <p>Explicit response DTOs keep lazy loading and schema evolution from leaking into the API boundary.</p>
  </div>
  <div class="check-card">
    <h3>Use SAVEPOINTs intentionally</h3>
    <p>`begin_nested()` is useful for tests and recovery patterns, not as a default request style.</p>
  </div>
</div>

## Official Sources

- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
