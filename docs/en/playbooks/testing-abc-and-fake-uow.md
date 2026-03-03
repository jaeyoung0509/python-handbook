# ABC + Fake UoW Testing

<p class="lead">If every use-case test goes all the way through SQLAlchemy and a real database, the suite gets slower and the failure signal becomes muddy. With `abc.ABC` boundaries and a fake Unit of Work, you can test commit policy, branching, and side-effect ordering very quickly without pretending that the database layer no longer matters.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: use `FakeUnitOfWork` and `RecordingNotifier` fixtures for fast use-case tests, and keep real Session/flush/loading/constraint behavior in integration tests. A fake is a tool for testing business branching, not a full replacement for SQLAlchemy behavior.</p>
</div>

## Start from the Fixture Graph

<MermaidDiagram
  caption="Even unit tests should read like a dependency graph: pytest fixtures assemble the fake UoW and fake notifier, and the test body consumes the use case."
  chart="flowchart TB; A[uow fixture] --> C[use_case fixture]; B[notifier fixture] --> C; C --> D[test body];"
/>

## What Fake UoW Tests Are Good At

- verifying that duplicate input does not commit
- verifying that success triggers exactly one notification
- verifying side effects happen after commit
- keeping the use case independent from SQLAlchemy details

## What Fake UoW Tests Cannot Prove

- real `Session.flush()` and `commit()` behavior
- ORM mapping, relationship loading, and constraint failures
- database isolation or lock behavior
- query counts, N+1 issues, and lazy-loading accidents

Those belong in integration tests.

## Recommended Shape

```py
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Self


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserRecord | None: ...

    @abstractmethod
    def add(self, user: UserRecord) -> None: ...


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
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
```

## Let pytest Fixtures Assemble the Graph

```py
import pytest


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def use_case(
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        uow_factory=lambda: uow,
        notifier=notifier,
    )
```

<p class="code-caption">The value of this pattern is that tests stop repeating composition code. Fixtures own the graph, while test bodies focus on business rules.</p>

## Separate Success and Failure Tests

```py
def test_register_user_commits_and_notifies(
    use_case: RegisterUserUseCase,
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> None:
    result = use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))

    assert result.email == "neo@example.com"
    assert uow.committed is True
    assert notifier.calls == [("neo@example.com", "Neo")]


def test_duplicate_email_rolls_back_and_skips_notification(
    use_case: RegisterUserUseCase,
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> None:
    uow.users.add(UserRecord(email="neo@example.com", name="Neo"))

    with pytest.raises(DuplicateEmail):
        use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))

    assert uow.committed is False
    assert uow.rolled_back is True
    assert notifier.calls == []
```

## When `monkeypatch` Helps

- environment-variable tests
- global reads such as time or UUID generation
- import-time side-effect control

If an `ABC` boundary already exists, a fake object is usually clearer than `monkeypatch`. Fakes preserve the architectural contract explicitly; monkeypatching is more name-replacement oriented.

## When to Escalate to Integration Tests

### Fake UoW is enough for

- business branching
- commit or no-commit policy
- whether side effects fire
- domain-error translation

### Use integration tests for

- unique constraints and real DB errors
- generated primary keys after `flush()`
- relationship loading behavior
- rollback effects in the actual database

## Examples in This Repository

- unit test example: `tests/test_abc_fake_uow_pytest.py`
- boundary design chapter: [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)
- DB-backed fixture example: `tests/test_fastapi_fixtures_and_teardown.py`

## Avoid These Patterns

- expecting one fake UoW suite to prove SQLAlchemy behavior
- copy-pasting use-case composition into every test body
- hiding notifier behavior behind monkeypatches when a fake object would be clearer
- mixing unit-test and integration-test responsibilities into one file

## Official References

- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [abc — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
