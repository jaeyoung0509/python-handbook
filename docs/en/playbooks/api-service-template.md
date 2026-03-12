# API Service Template

<p class="lead">Small FastAPI services are easy to start, but route functions can accumulate validation, transactions, logging, ORM access, and external API calls surprisingly quickly. This chapter proposes a service skeleton that is not "perfect architecture," but one that tends to age with less regret.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: the goal is not to maximize layers. The goal is to keep boundaries explicit. Let routes behave like transport adapters, services orchestrate use cases, repositories own persistence details, schemas define contracts, and settings/logging/lifespan define infrastructure boundaries.</p>
</div>

## One-Page Structural View

<MermaidDiagram
  caption="Splitting HTTP, application, persistence, and infrastructure responsibilities keeps change paths clearer as a FastAPI service grows."
  chart="flowchart LR; A[Router and DTOs] --> B[Service or Use Case]; B --> C[Repository]; C --> D[Session and Database]; A --> E[Auth and Dependency Wiring]; E --> B; F[Settings and Lifespan] --> E; F --> D;"
/>

## Suggested Folder Layout

```text
app/
  api/
    routes/
      users.py
      health.py
  schemas/
    user.py
  services/
    user_service.py
  repositories/
    user_repository.py
  db/
    models.py
    session.py
  domain/
    errors.py
  core/
    config.py
    logging.py
  main.py
tests/
  integration/
  unit/
```

## What Each Layer Should Know

| Layer | Responsibility | Should not know |
| --- | --- | --- |
| route | HTTP input/output, auth, status codes, response model | ORM details, commit policy |
| schema | request/response contract | DB sessions, external API calls |
| service | business action orchestration, transaction boundary | framework-specific HTTP details |
| repository | query shape, persistence details | HTTP status and serialization contract |
| core/infrastructure | settings, logging, lifespan, clients | business branching |

## Let the App Entrypoint Handle Wiring

```py
from fastapi import FastAPI

from app.api.routes import health, users
from app.core.config import Settings, get_settings
from app.db.session import lifespan


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(users.router)
    return app


app = create_app()
```

<p class="code-caption">`main.py` should be a wiring entrypoint, not a business layer. It usually owns settings, router registration, and lifespan configuration, while domain rules stay elsewhere.</p>

## Settings and Logging Are Boundaries Too

- read settings once and inject them, rather than scattering environment lookups
- define logging strategy around request IDs, domain events, and error boundaries early
- pass settings through factories or dependencies so tests can replace them cleanly

For deeper guidance on `settings.py` and `pydantic-settings`, see [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings). For hosting tradeoffs, see [Lambda vs Kubernetes](/en/playbooks/lambda-vs-kubernetes).

## Split the Test Layout Early

### unit tests

- pure business rules
- service branching
- typing boundaries and serialization behavior

### integration tests

- HTTP contracts
- dependency overrides
- DB session lifecycle
- real serialization output

## Rules for a Service That Ages Well

1. Keep routes thin.
2. Let services or use cases own commits.
3. Treat ORM entities as internal details and finish with DTOs.
4. Separate background work from request paths.
5. Add observability and timeouts early.

## sub-optimal -> improved: where service skeletons usually break first

### Bad example: route, settings, persistence, and side effects collapsed together

```py
import os

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.post("/orders")
async def create_order(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_session),
) -> OrderRead:
    if os.getenv("ALLOW_ORDERING", "true") != "true":
        raise HTTPException(status_code=503, detail="ordering disabled")

    order = OrderModel.model_validate(payload)
    session.add(order)
    await session.commit()
    await publish_order_created(order.id)
    return OrderRead.model_validate(order)
```

<p class="code-caption">This feels fast at first, but ordering policy, transaction boundaries, event timing, and DTO stability all become route-level concerns. As retry, timeout, idempotency, or audit requirements appear, the route turns into a giant function representing the whole service.</p>

### Better example: route as transport, service as action orchestration

```py
@router.post("/orders", response_model=OrderRead)
async def create_order(
    payload: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    command = CreateOrderCommand.model_validate(payload)
    return await service.create_order(command)


class OrderService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        publisher: OrderPublisher,
    ) -> None:
        self.session = session
        self.settings = settings
        self.publisher = publisher

    async def create_order(self, command: CreateOrderCommand) -> OrderRead:
        if not self.settings.allow_ordering:
            raise OrderingDisabled()

        order = OrderModel.from_command(command)
        self.session.add(order)
        await self.session.commit()
        await self.publisher.publish_created(order.id)
        return OrderRead(id=order.id, status=order.status)
```

<p class="code-caption">The goal is not "more layers." The goal is readable ownership. Once routes behave like transport adapters, services represent business actions, and settings plus publishers are explicit boundaries, refactoring and incident response both become easier.</p>

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Entrypoint is for wiring</h3>
    <p>The app factory should compose routers and infrastructure, not implement domain behavior directly.</p>
  </div>
  <div class="check-card">
    <h3>Service owns transaction completion</h3>
    <p>Repositories should not commit autonomously if you want multi-step business actions to remain atomic.</p>
  </div>
  <div class="check-card">
    <h3>Tests follow the same boundaries</h3>
    <p>Lifespan, dependency overrides, and rollback strategies should mirror the service's real structure.</p>
  </div>
  <div class="check-card">
    <h3>Settings and logging are designed</h3>
    <p>Early structure around configuration and observability reduces later operational pain.</p>
  </div>
</div>

## Code Review Lens

- Check whether the route stays transport-oriented while the service represents the business action.
- Check whether settings and env reads are organized at wiring boundaries instead of scattered through service code.
- Check whether repositories know query and persistence details but not commit policy.
- Check whether external side effects happen only after durable commit.

## Common Anti-Patterns

- doing env lookup, querying, committing, publishing, and serializing directly in a route
- helpers or repositories committing implicitly and breaking transaction atomicity
- using ORM entities directly as request or response schemas
- postponing observability, timeout, and retry structure until the entrypoint is already bloated

## Likely Discussion Questions

- Where would this structure break first if you had to add feature flags, audit logs, or an outbox?
- Why should commit ownership live at the service or use-case boundary instead of the repository?
- What boundaries must remain stable if background jobs and workers should reuse the same business action?
- What cost appears in tests and operations once service code reads env vars directly?

## Strong Answer Frame

- Start by separating responsibilities across route, service, repository, and infrastructure boundaries.
- Explain the concrete cost of the current shape: partial commits, oversized tests, and weak operational visibility.
- Restore settings injection, service orchestration, and DTO boundaries with the smallest refactor that changes ownership clearly.
- Close by showing where retry, idempotency, and observability will attach once the boundaries are explicit.

## Good Supporting Examples

- `examples/fastapi_service_template_example.py`
- `examples/sqlalchemy_loading_strategies.py`
- `examples/sqlalchemy_class_based_uow.py`
- `tests/test_fastapi_fixtures_and_teardown.py`

## Refactoring Path

- If you want a fast map of recurring smells first, start with [Refactoring Atlas](/en/playbooks/refactoring-atlas).
- For the concrete route and dependency cleanup flow, continue with [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage).

## Official References

- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
