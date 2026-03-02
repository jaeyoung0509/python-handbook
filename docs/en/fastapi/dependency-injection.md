# Dependency Injection

<p class="lead">FastAPI's DI system is not just a syntax for `Depends`. It is the wiring layer that decides where sessions, settings, auth principals, and external clients are created and where they are cleaned up. Once that layer leaks business policy, your service code becomes framework-shaped instead of domain-shaped.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: dependencies should wire resources and boundaries, not own business logic or transaction policy. Keep DI boring and your service layer explicit.</p>
</div>

## See the Dependency Graph Clearly

<MermaidDiagram
  caption="Dependencies provide resources to the router layer, but business rules still belong in services."
  chart="flowchart LR; A[Request] --> B[Router]; B --> C[Depends(get_session)]; B --> D[Depends(get_current_user)]; C --> E[Session]; E --> F[Service]; D --> F; F --> G[Response DTO];"
/>

## The Most Important Pattern: Yield Dependencies

```py
from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(session)
```

<p class="code-caption">Use a `yield` dependency for resources that must be opened and closed. Constructing a service object is cheap and usually needs no cleanup, so a regular dependency function is enough.</p>

## What Belongs in Dependencies and What Does Not

| Fine inside dependencies | Better left to services |
| --- | --- |
| DB session lifecycle | business rules |
| settings objects | transaction policy |
| auth principal extraction | domain validation |
| external client lifecycle | response assembly |

## Test Overrides Are Part of the Design

```py
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_test_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = get_test_session
```

## Practical Rules

- Dependencies are resource providers, not business layers.
- Use `yield` dependencies for request-scoped resources that must be cleaned up.
- Build services in dependencies if that keeps routers thin, but keep branching logic inside service methods.
- Background jobs, schedulers, and CLIs need their own session lifecycle outside FastAPI's dependency graph.

## Official Sources

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
