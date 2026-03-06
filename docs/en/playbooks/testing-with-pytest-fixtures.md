# Testing with Fixtures

<p class="lead">Good tests are often decided less by the assertion line and more by fixture design. If database setup, app creation, dependency overrides, clients, and teardown rules are unclear, a test suite quickly becomes slow, flaky, and full of hidden coupling.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: in pytest, treat `yield` fixtures as the default. Keep teardown directly below the `yield`, split app, DB, client, and override concerns into separate fixtures, and let test bodies consume that graph instead of rebuilding it ad hoc.</p>
</div>

## Start from the Fixture Graph

<MermaidDiagram
  caption="Fixture ownership should read like a dependency graph: outer resources open first, inner fixtures consume them, and teardown runs in reverse order."
  chart="flowchart TB; A[engine fixture] --> B[session_factory fixture]; B --> C[app fixture]; C --> D[client fixture]; B --> E[seed data fixture]; D --> F[test body]; E --> F;"
/>

## Baseline Rules

- fixtures create and own resources
- tests consume those resources to verify behavior
- teardown lives directly below the `yield`
- mutable global state should not leak across tests

## A Readable Default Pattern

```py
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: TestSettings()
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
```

<p class="code-caption">The key point is that cleanup stays next to setup. That makes ownership obvious: the fixture that installs the override is also the fixture that removes it.</p>

## Database Fixtures Need an Explicit Isolation Strategy

### Smaller services or early-stage projects

- function-scoped SQLite
- schema create/drop per test
- slower, but very easy to reason about

### Larger services

- connection + transaction + rollback
- nested SAVEPOINT when needed
- better throughput without giving up clear isolation

## With testcontainers, separate container lifetime from test isolation

Once teams adopt `testcontainers`, they often mix two different concerns into one fixture:

- starting a PostgreSQL container
- resetting database state so each test stays isolated

Those are not the same job.

- the container lifecycle usually belongs to an outer fixture
- schema setup, seeding, rollback, or truncation belong to inner fixtures

### A practical baseline

- make the container `session`-scoped or `module`-scoped
- place the engine and session factory inside that boundary
- keep test isolation function-scoped through rollback or truncate-plus-seed

Starting a fresh container per test is simple, but usually too slow. Sharing a long-lived container without a reset strategy creates flaky integration tests.

### A readable example

```py
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:17") as container:
        yield container


@pytest.fixture(scope="session")
def engine(postgres_container: PostgresContainer) -> Generator[Engine, None, None]:
    test_engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    testing_session = sessionmaker(
        bind=connection,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )()

    try:
        yield testing_session
    finally:
        testing_session.close()
        transaction.rollback()
        connection.close()
```

<p class="code-caption">The important idea is that the outer fixture owns container startup cost, while the function-scoped `db_session` owns per-test isolation. Do not collapse startup and isolation into one giant fixture.</p>

### When FastAPI is also involved

1. `postgres_container` starts a real Postgres instance.
2. `engine` prepares schema or migrations.
3. `db_session` defines rollback isolation per test.
4. `app` injects that session or session factory through `dependency_overrides`.
5. `client` opens and closes `TestClient`.

### When should real migrations run?

- if you only need repository or ORM query-shape validation, `metadata.create_all()` can be enough
- if you want to validate Alembic revisions, indexes, constraints, or DB-specific DDL, run real migrations against the container instead

So "use real Postgres" and "verify the real migration path" are separate decisions.

### Practical rules

- do not place the container at too narrow a scope
- put test isolation in rollback, truncate, or seed fixtures instead
- keep app override cleanup under the `yield` that installed it
- share expensive container startup across the suite, but keep per-test resources short-lived inside it
- in async stacks, keep the container fixture shared and define separate async engine or session fixtures inside it

## Why `yield` Fixtures Are the Default

The pytest docs explicitly present `yield` fixtures as the cleaner and more straightforward teardown option. `addfinalizer()` is still useful for dynamically registered cleanup, but most application tests are easier to read and maintain with `yield`.

The complementary `ABC + Fake UoW` unit-testing pattern is covered separately in [ABC + Fake UoW Testing](/en/playbooks/testing-abc-and-fake-uow).

## Patterns to Avoid

- one giant `autouse` fixture that hides the whole environment
- mutating `dependency_overrides` inside test bodies without centralized cleanup
- reusing global sessions or clients across tests
- hiding teardown rules far away from setup
- mixing DB seeding and external API stubs into one catch-all fixture
- collapsing container startup and per-test DB reset into one oversized fixture

## A Practical Test Layout

```text
tests/
  conftest.py
  integration/
    test_users_api.py
  unit/
    test_user_service.py
```

- `conftest.py`: shared fixture graph
- `integration/`: HTTP contracts, DB, serialization
- `unit/`: pure service and domain behavior

## Example in This Repository

This repository now includes `tests/test_fastapi_fixtures_and_teardown.py`, which demonstrates:

- engine fixture creation and teardown
- seed fixtures
- installing and clearing `dependency_overrides`
- `TestClient` lifecycle cleanup

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Fixtures own resource lifecycles</h3>
    <p>You should be able to see who opens and who closes a resource by reading the fixture alone.</p>
  </div>
  <div class="check-card">
    <h3>Overrides are cleaned up</h3>
    <p>FastAPI dependency overrides belong in fixture teardown, not in loose test cleanup code.</p>
  </div>
  <div class="check-card">
    <h3>DB isolation is explicit</h3>
    <p>Teams should choose intentionally between recreate-and-drop and rollback-based isolation.</p>
  </div>
  <div class="check-card">
    <h3>Container scope and reset strategy are separate</h3>
    <p>When using `testcontainers`, keep container lifetime and per-test isolation in different fixtures.</p>
  </div>
  <div class="check-card">
    <h3>`autouse` stays minimal</h3>
    <p>Hidden fixture behavior should be reserved for true shared infrastructure, not everyday test logic.</p>
  </div>
</div>

## Official References

- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest fixture finalization](https://docs.pytest.org/en/stable/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [testcontainers-python](https://testcontainers-python.readthedocs.io/en/latest/)
