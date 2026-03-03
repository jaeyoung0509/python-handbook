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

## Good Supporting Examples

- `examples/fastapi_service_template_example.py`
- `examples/sqlalchemy_loading_strategies.py`
- `examples/sqlalchemy_class_based_uow.py`
- `tests/test_fastapi_fixtures_and_teardown.py`

## Official References

- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
