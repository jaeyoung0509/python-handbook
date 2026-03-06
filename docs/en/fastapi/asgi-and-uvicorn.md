# ASGI and Uvicorn

<p class="lead">To use FastAPI well, you need to understand its runtime boundary before focusing on route syntax. FastAPI is not the server. It is an ASGI application. Uvicorn is the ASGI server that connects that application to real sockets, HTTP traffic, WebSocket connections, and process lifecycle.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: Uvicorn accepts connections, runs the event loop, parses HTTP or WebSocket traffic, and calls the application through ASGI `scope`, `receive`, and `send`. FastAPI and Starlette sit on top of that and handle routing, dependency injection, validation, and serialization. You need this split to reason about workers, timeouts, proxies, and lifespan behavior.</p>
</div>

## The full request path

<MermaidDiagram
  caption="A FastAPI request does not start inside the route function. It flows through sockets, the ASGI server, middleware, dependencies, and response events."
  chart="flowchart LR; A[&quot;Socket accepted by Uvicorn&quot;] --> B[&quot;HTTP or WebSocket parser&quot;]; B --> C[&quot;ASGI scope and receive events&quot;]; C --> D[&quot;Starlette middleware stack&quot;]; D --> E[&quot;FastAPI routing and dependencies&quot;]; E --> F[&quot;Response or websocket messages&quot;]; F --> G[&quot;Uvicorn writes bytes to client&quot;];"
/>

## Separate FastAPI from Uvicorn

| Layer | Main responsibility | Questions that belong here |
| --- | --- | --- |
| Uvicorn | socket acceptance, event loop, protocol parsing, connection timeout, worker processes | keep-alive, graceful shutdown, proxy headers, concurrency limits |
| ASGI contract | `scope`, `receive`, `send`, plus `http`/`websocket`/`lifespan` | what event flow is actually happening |
| Starlette/FastAPI | middleware, routing, dependencies, validation, serialization, exception handling | how thin routes should be, where resource ownership belongs |

## Start with the smallest ASGI shape

```py
async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    message = await receive()
    assert message["type"] == "http.request"

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b"hello from ASGI",
        }
    )
```

<p class="code-caption">The important point is that the app does not receive a framework request object directly. It receives a general protocol interface. FastAPI builds richer request and dependency abstractions on top of that interface.</p>

## What Uvicorn actually owns

### 1. It accepts connections and calls the ASGI app

- It handles TCP connections and HTTP or WebSocket protocol parsing.
- It turns parsed protocol data into ASGI `scope` values and inbound events.
- It turns ASGI response messages back into bytes on the wire.

### 2. It coordinates lifespan at the server level

- It opens lifespan on startup.
- It closes lifespan on shutdown.
- In multi-worker setups, each worker should be treated as running its own lifespan sequence.

### 3. It owns critical operational settings

| Setting | Meaning | When it matters | Common mistake |
| --- | --- | --- | --- |
| `--reload` | restarts on code changes | local development | leaving it on in production |
| `--workers` | process count | CPU usage and isolation | increasing it without DB pool math |
| `--proxy-headers` | trust forwarded proxy headers | production behind ingress or Nginx | misreading client IP or scheme |
| `--timeout-keep-alive` | idle keep-alive duration | controlling connection churn | changing it blindly |
| `--timeout-graceful-shutdown` | shutdown grace period | rolling deploys and draining | cutting requests during shutdown |
| `--limit-concurrency` | server-side concurrency cap | downstream protection | relying only on app-level semaphores |

## Common points of confusion

### Worker count and coroutine count are different axes

- Workers are processes.
- Coroutines are scheduled tasks inside a worker event loop.
- Raising worker count does not automatically make route code proportionally faster.

### `app.state` is not shared memory across workers

- Each worker is a separate process.
- Engines, clients, and in-memory caches created in lifespan exist per worker.
- Assumptions like "this initializes only once" often break in multi-worker deployments.

### Route code is not server behavior

- Timeouts, keep-alive behavior, proxy handling, and graceful shutdown live in the ASGI server layer.
- Validation, dependency graphs, and response modeling live in FastAPI and Starlette.

## Basic environment profiles to distinguish

### Local development

- `uvicorn app.main:app --reload`
- prioritize fast iteration
- do not trust local performance numbers

### Simple container deployment

- disable reload
- size workers together with DB connection budgets
- configure forwarded headers explicitly when behind a proxy

### WebSocket or streaming-heavy services

- understand ASGI connection lifetime first
- long-lived ASGI servers are often a more natural fit than request-only runtimes
- revisit timeout, shutdown, and background-work assumptions with connection lifetime in mind

## What to read next

1. [Lifespan and Testing](/en/fastapi/lifespan-and-testing)
2. [Background Tasks and Offloading](/en/fastapi/background-tasks-and-offloading)
3. [Performance and Ops](/en/fastapi/performance-and-ops)

For runnable intuition, pair this chapter with `examples/asgi_lifecycle_lab.py`.

## Official References

- [ASGI Specification](https://asgi.readthedocs.io/en/latest/specs/main.html)
- [ASGI Introduction](https://asgi.readthedocs.io/en/latest/introduction.html)
- [Uvicorn Settings](https://www.uvicorn.org/settings/)
- [Uvicorn Server Behavior](https://www.uvicorn.org/server-behavior/)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
