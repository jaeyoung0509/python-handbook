# FastAPI

<p class="lead">This part treats FastAPI as a boundary-design framework, not just a quick way to expose endpoints. The important questions are where HTTP concerns stop, where services begin, how request-scoped resources are owned, and how Pydantic, SQLAlchemy, and asyncio fit together without collapsing into one layer.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: using FastAPI well means keeping routes thin, wiring resources explicitly, owning request lifecycles, and preserving stable DTO contracts. The framework is most effective when HTTP concerns and application concerns stay separate.</p>
</div>

## The Questions to Anchor First

<div class="reading-grid">
  <div class="reading-card">
    <h3>How much should a route know?</h3>
    <p>Mostly HTTP parsing, auth, and response contracts. Domain rules and commit policy should stay deeper inside.</p>
  </div>
  <div class="reading-card">
    <h3>What should dependencies do?</h3>
    <p>They should wire sessions, settings, and clients. They should not become a hidden business layer.</p>
  </div>
  <div class="reading-card">
    <h3>Does async make it fast automatically?</h3>
    <p>No. Blocking calls, validation cost, query shape, pool sizing, and serialization dominate most real bottlenecks.</p>
  </div>
  <div class="reading-card">
    <h3>What should tests prove?</h3>
    <p>Resource lifecycles, dependency overrides, transaction isolation, and response contracts are usually more important than route internals.</p>
  </div>
</div>

## Recommended Reading Order

1. [Project Structure](/en/fastapi/project-structure)
2. [Dependency Injection](/en/fastapi/dependency-injection)
3. [Request/Response Modeling](/en/fastapi/request-response-modeling)
4. [Lifespan and Testing](/en/fastapi/lifespan-and-testing)
5. [Performance and Ops](/en/fastapi/performance-and-ops)

## Working Rules for Real Services

- Keep routes thin and transport-oriented.
- Do not collapse request DTOs, domain commands, ORM entities, and response DTOs into one type.
- Use lifespan or `yield` dependencies for resource ownership.
- Do not hide sync blocking work inside `async` endpoints.
- Look at query shape, serialization cost, pool contention, and observability before blaming framework overhead.

## Good Companion Chapters

- [Asyncio](/en/asyncio/)
- [Pydantic](/en/pydantic/)
- [SQLAlchemy 2.0](/en/sqlalchemy/)
- [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
