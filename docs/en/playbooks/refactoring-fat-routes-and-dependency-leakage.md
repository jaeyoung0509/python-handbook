# Refactoring Fat Routes and Dependency Leakage

<p class="lead">Fat routes and dependency leakage usually arrive together. A route should behave like a transport adapter and a dependency should behave like resource wiring. Once those boundaries erode, validation, auth, policy, queries, commits, and serialization all collapse into one request path.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: the safest repair sequence is `remove business branching from the route -> make the dependency boring again -> gather action ownership inside a service or use case`. You do not need to rewrite the whole folder structure to make the code healthier.</p>
</div>

## 1) sub-optimal snippet

```py
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_checkout_service(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> "CheckoutService":
    if os.getenv("CHECKOUT_DISABLED", "false") == "true":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    service = CheckoutService(session)
    await service.prepare_cart_for(user.user_id)
    await session.commit()
    return service


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> CheckoutResponse:
    if payload.total <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    existing = await session.scalar(
        select(OrderRecord).where(OrderRecord.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        return CheckoutResponse.model_validate(existing)

    if user.plan == "free" and payload.total > 100:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    record = OrderRecord(user_id=user.user_id, total=payload.total)
    session.add(record)
    await session.commit()
    return CheckoutResponse.model_validate(record)
```

## 2) What is the exact smell?

- The route owns business branching and transaction policy instead of only HTTP concerns.
- The dependency owns policy branching and side effects instead of only resource wiring.
- Settings lookup, idempotency queries, commits, and DTO assembly are mixed into the same request path.

This can feel fast early on, but as soon as timeouts, tracing, audit logging, retries, or feature flags appear, every change spreads across the route and dependency boundary.

## 3) The smallest safe refactor sequence

1. Move business branching and commit ownership out of the route into a service or use case.
2. Shrink dependencies until they only assemble sessions, settings, principals, and clients.
3. Translate domain errors to HTTP in the route or in exception handlers.
4. Leave the route with only DTO-to-command translation and response DTO output.

The goal is not "more layers." The goal is restoring one ownership boundary at a time.

## 4) improved end state

```py
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_checkout_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[CurrentUser, Depends(get_current_user)],
) -> "CheckoutService":
    return CheckoutService(
        session=session,
        settings=settings,
        principal=principal,
    )


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutRequest,
    service: Annotated["CheckoutService", Depends(get_checkout_service)],
) -> CheckoutResponse:
    command = CheckoutCommand(
        idempotency_key=payload.idempotency_key,
        total=payload.total,
    )
    return await service.checkout(command)


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

    async def checkout(self, command: CheckoutCommand) -> CheckoutResponse:
        if not self.settings.checkout_enabled:
            raise CheckoutDisabled()
        if self.principal.is_suspended:
            raise PermissionDenied()
        if self.principal.plan == "free" and command.total > 100:
            raise PlanLimitExceeded()

        existing = await self.session.scalar(
            select(OrderRecord).where(OrderRecord.idempotency_key == command.idempotency_key)
        )
        if existing is not None:
            return CheckoutResponse.model_validate(existing)

        record = OrderRecord(user_id=self.principal.user_id, total=command.total)
        self.session.add(record)
        await self.session.commit()
        return CheckoutResponse.model_validate(record)
```

## 5) What gets better

- `tests`: routes can focus on transport contracts while services focus on business branching.
- `operations`: it becomes much clearer where tracing, timeout policy, and audit logging belong.
- `change isolation`: policy or settings changes no longer force broad edits across HTTP wiring.

## Code Review Lens

- Check whether the route knows only request parsing, auth boundary, and response contract.
- Check whether the dependency only wires resources and boundaries.
- Check whether one service or use case clearly represents one business action.
- Check whether settings lookup and principal restoration arrive as explicit inputs.

## Common Anti-Patterns

- dependencies reading feature flags and throwing HTTP exceptions directly
- routes doing domain branching, queries, commits, and response assembly in one place
- hiding sync client calls or secret lookups inside `async` endpoints
- trying to solve fat routes with a giant all-at-once folder rewrite

## Likely Discussion Questions

- Which responsibility should move out of the route first for the safest refactor?
- What does it concretely mean to make a dependency "boring" again?
- When should domain errors start moving into exception handlers?
- How does a cleaner service boundary help reuse from background jobs or CLIs?

## Strong Answer Frame

- Start by classifying mixed responsibilities across route and dependency boundaries.
- Then move business branching and commit ownership inward in the smallest possible steps.
- Explain how separating HTTP concerns from application concerns improves tests and operational clarity.
- Close by noting the next extensions that become easier: exception handlers, audit logging, or outbox patterns.

## Good companion chapters

- [Refactoring Atlas](/en/playbooks/refactoring-atlas)
- [Project Structure](/en/fastapi/project-structure)
- [Dependency Injection](/en/fastapi/dependency-injection)
- [API Service Template](/en/playbooks/api-service-template)
