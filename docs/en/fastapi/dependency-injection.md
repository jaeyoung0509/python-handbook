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

## sub-optimal -> improved: when dependencies turn into business layers

### Bad example: the dependency owns branching and commit policy

```py
import os

from fastapi import Depends, HTTPException, status


async def get_checkout_service(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> CheckoutService:
    if os.getenv("CHECKOUT_DISABLED", "false") == "true":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    service = CheckoutService(session)
    await service.prepare_cart_for(user.user_id)
    await session.commit()
    return service
```

<p class="code-caption">This dependency now owns config lookup, policy branching, service side effects, and commit behavior. DI stops being framework wiring and starts becoming a hidden business layer, which makes overrides and tests much more expensive.</p>

### Better example: keep the dependency boring

```py
from typing import Annotated

from fastapi import Depends


def get_checkout_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[CurrentUser, Depends(get_current_user)],
) -> CheckoutService:
    return CheckoutService(
        session=session,
        settings=settings,
        principal=principal,
    )


class CheckoutService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        principal: CurrentUser,
    ) -> None:
        self.session = session
        self.settings = settings
        self.principal = principal

    async def checkout(self, command: CheckoutCommand) -> CheckoutResult:
        if not self.settings.checkout_enabled:
            raise CheckoutDisabled()
        if self.principal.is_suspended:
            raise PermissionDenied()
        ...
```

<p class="code-caption">The key improvement is making the dependency boring. DI assembles resources and boundaries, while business branching and transaction policy remain visible inside the service or use case.</p>

## Practical Rules

- Dependencies are resource providers, not business layers.
- Use `yield` dependencies for request-scoped resources that must be cleaned up.
- Build services in dependencies if that keeps routers thin, but keep branching logic inside service methods.
- Background jobs, schedulers, and CLIs need their own session lifecycle outside FastAPI's dependency graph.

## Code Review Lens

- Check whether the dependency stops at wiring sessions, settings, principals, and clients.
- Check whether `yield` dependencies really guarantee cleanup for request-scoped resources.
- Check whether service construction is separated from business branching.
- Check whether FastAPI-specific types stay out of service and use-case signatures.

## Common Anti-Patterns

- a dependency reading feature flags and deciding HTTP errors directly
- a dependency calling `commit()` or making external side effects before the service runs
- CLIs, schedulers, or background workers trying to reuse FastAPI dependency lifecycles
- stuffing resource supply, authorization policy, and domain branching into one dependency chain

## Likely Discussion Questions

- What logic belongs in a dependency, and what should move into a service?
- What does a missing `yield` cleanup path look like in production?
- How do you design dependencies so tests only need to swap values, not replay whole workflows?
- If the same service must run in HTTP and background jobs, where should it stop depending on FastAPI DI?

## Strong Answer Frame

- Define dependency responsibility first in terms of resource ownership and boundary wiring.
- Point out the testing and operational costs once business logic leaks into DI.
- Separate resources that need cleanup from objects that only need construction.
- Validate the design by checking whether the same service can run from HTTP, CLI, and worker entrypoints.

## Refactoring Path

- Use [Refactoring Atlas](/en/playbooks/refactoring-atlas) for the quick smell map.
- For the concrete cleanup sequence, continue with [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage).

## Official Sources

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
