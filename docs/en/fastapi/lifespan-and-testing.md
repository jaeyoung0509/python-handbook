# Lifespan and Testing

<p class="lead">A FastAPI service is not just request handlers. It also owns engines, HTTP clients, caches, settings, and sometimes background workers. Unless startup, shutdown, and request-scoped resources are modeled explicitly, production and test environments drift apart very quickly.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: prefer the lifespan API for process-wide resources and `yield` dependencies for request-scoped resources. Then make tests pass through the same lifecycle boundaries, so your test environment behaves like the service you actually run.</p>
</div>

## The Big Picture

<MermaidDiagram
  caption="Application lifespan and request lifespan are different scopes. Shared resources belong to the app lifespan; sessions and principals usually belong to request dependencies."
  chart="flowchart LR; A[App startup] --> B[Lifespan opens shared resources]; B --> C[Requests arrive]; C --> D[Request dependency opens session]; D --> E[Handler and service work]; E --> F[Dependency cleanup closes session]; F --> G[App shutdown]; G --> H[Lifespan closes engine, clients, caches];"
/>

## What Belongs in Lifespan

### Good lifespan resources

- SQLAlchemy engine or async engine
- shared `httpx.AsyncClient`
- Redis or broker clients
- warmed configuration and caches

### Good request-scoped dependencies

- `Session` / `AsyncSession`
- current authenticated principal
- request-scoped trace context
- service instances composed from those resources

## Recommended Pattern: app state plus dependency

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_async_engine(
        "postgresql+asyncpg://app:secret@localhost/app",
        pool_pre_ping=True,
    )
    app.state.session_factory = async_sessionmaker(
        engine,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(lifespan=lifespan)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
```

<p class="code-caption">The engine is process-wide, so it belongs to lifespan. The session is request-scoped, so it should be created per request. `app.state` is for shared infrastructure, not for mutable business state.</p>

## Why Tests Should Traverse Lifespan Too

Using `TestClient(app)` or an ASGI transport within a context manager triggers lifespan startup and shutdown. If tests skip that boundary, they can silently run against an application state that does not resemble production.

```py
from fastapi.testclient import TestClient


def test_healthcheck() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
```

## Dependency Overrides Are a Boundary Tool

```py
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_test_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = get_test_session
```

- Use overrides to replace DB/session providers or external clients intentionally.
- Restore overrides after tests.
- Treat overrides as part of API boundary design, not just as a mocking trick.

## Async Integration Test Pattern

```py
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_register_user() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/users",
            json={"email": "neo@example.com", "name": "Neo"},
        )

    assert response.status_code == 201
    assert response.json()["email"] == "neo@example.com"
```

## Designing Database Tests

| Question | Recommended direction | Fragile pattern |
| --- | --- | --- |
| How is DB state prepared? | fixture-level schema setup or rollback isolation | every test reruns migrations blindly |
| How is session isolation enforced? | SAVEPOINT, dedicated test DB, deterministic seed | global session reuse |
| What does the test verify? | status, response shape, side effects | route implementation details |
| How are external APIs replaced? | provider or client overrides | calling real production endpoints |

## Let Fixtures Own Setup and Teardown

- `yield` fixtures make setup and teardown ownership easiest to read.
- `app.dependency_overrides` should be cleared in fixture teardown, not forgotten inside tests.
- `TestClient` is more reliable when opened and closed inside a fixture context manager.
- For a longer example, read [Testing with Fixtures](/en/playbooks/testing-with-pytest-fixtures) alongside `tests/test_fastapi_fixtures_and_teardown.py`.

## Common Mistakes

- Creating a session at startup and reusing it globally.
- Skipping lifespan during tests so app state is never initialized correctly.
- Leaving `dependency_overrides` installed after a test.
- Mixing sync and async client patterns without a clear event-loop model.

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Shared resources in lifespan</h3>
    <p>Engines, clients, caches, and other process-wide resources should open and close in one explicit place.</p>
  </div>
  <div class="check-card">
    <h3>Request resources in dependencies</h3>
    <p>Sessions and principals fit naturally into `yield` dependencies because cleanup is tied to the request.</p>
  </div>
  <div class="check-card">
    <h3>Production and tests share boundaries</h3>
    <p>Use the same lifespan and dependency structure in tests so you are not validating a fake application model.</p>
  </div>
  <div class="check-card">
    <h3>External dependencies are replaceable</h3>
    <p>Services should accept providers or clients from the outside so tests can swap them cleanly.</p>
  </div>
</div>

## Official References

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
