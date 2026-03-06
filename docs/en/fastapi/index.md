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
    <h3>Why learn ASGI and Uvicorn first?</h3>
    <p>FastAPI is not the server. If you do not understand scopes, receive/send events, workers, and lifespan, production behavior will stay opaque.</p>
  </div>
  <div class="reading-card">
    <h3>Does async make it fast automatically?</h3>
    <p>No. Blocking calls, validation cost, query shape, pool sizing, and serialization dominate most real bottlenecks.</p>
  </div>
  <div class="reading-card">
    <h3>Can anything go into `BackgroundTasks`?</h3>
    <p>No. Keep it for short in-process follow-up work. Durable or heavy work belongs in a queue and worker model.</p>
  </div>
  <div class="reading-card">
    <h3>How are websockets and streaming different?</h3>
    <p>They are not one-shot request/response paths. Connection lifetime, middleware behavior, timeouts, and shutdown rules all matter more.</p>
  </div>
  <div class="reading-card">
    <h3>How should real-time services be designed?</h3>
    <p>Plan auth on connect, room membership, disconnect cleanup, reconnect behavior, and multi-worker broadcast boundaries together.</p>
  </div>
  <div class="reading-card">
    <h3>What should tests prove?</h3>
    <p>Resource lifecycles, dependency overrides, transaction isolation, and response contracts are usually more important than route internals.</p>
  </div>
  <div class="reading-card">
    <h3>Where does observability start?</h3>
    <p>Connect OpenTelemetry, Sentry, and structured logging once at startup, then design request IDs, trace IDs, and sampling policy intentionally.</p>
  </div>
  <div class="reading-card">
    <h3>What changes behind a reverse proxy?</h3>
    <p>`root_path`, forwarded headers, readiness, and graceful shutdown become explicit operational concerns instead of local-only details.</p>
  </div>
</div>

## Recommended Reading Order

1. [ASGI and Uvicorn](/en/fastapi/asgi-and-uvicorn)
2. [Project Structure](/en/fastapi/project-structure)
3. [Dependency Injection](/en/fastapi/dependency-injection)
4. [Request/Response Modeling](/en/fastapi/request-response-modeling)
5. [Lifespan and Testing](/en/fastapi/lifespan-and-testing)
6. [Background Tasks and Offloading](/en/fastapi/background-tasks-and-offloading)
7. [WebSockets, Streaming, and Middleware](/en/fastapi/websockets-streaming-and-middleware)
8. [WebSocket Practical Patterns](/en/fastapi/websocket-practical-patterns)
9. [Proxy, Health, and Shutdown](/en/fastapi/proxy-health-and-shutdown)
10. [Performance and Ops](/en/fastapi/performance-and-ops)
11. [Observability](/en/fastapi/observability)

## Working Rules for Real Services

- Keep routes thin and transport-oriented.
- Separate the ASGI server's responsibilities from the FastAPI app's responsibilities.
- Do not collapse request DTOs, domain commands, ORM entities, and response DTOs into one type.
- Use lifespan or `yield` dependencies for resource ownership.
- Use `BackgroundTasks` only for short in-process follow-up work, not for durable or heavy jobs.
- Treat websockets and streaming as long-lived connection paths, not ordinary request handlers.
- Design WebSocket auth, room cleanup, and multi-worker broadcast strategy explicitly instead of treating them as incidental route details.
- Treat reverse proxies, health endpoints, and graceful shutdown as explicit operational boundaries.
- Do not hide sync blocking work inside `async` endpoints.
- Look at query shape, serialization cost, pool contention, and observability before blaming framework overhead.
- Configure tracing, error monitoring, and structured logging once during app bootstrap.

## Good Companion Chapters

- [Asyncio](/en/asyncio/)
- [Pydantic](/en/pydantic/)
- [SQLAlchemy 2.0](/en/sqlalchemy/)
- [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
