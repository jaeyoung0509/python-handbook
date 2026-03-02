# Performance and Ops

<p class="lead">FastAPI is fast, but real bottlenecks rarely live in the framework alone. Hidden blocking work, expensive validation and serialization, poor query shapes, pool contention, worker sizing, and missing observability dominate most production slowdowns.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: performance tuning starts with system boundaries, not with micro-optimizing route functions. Remove blocking work, tighten DTOs and queries, size pools and workers coherently, and add latency visibility before chasing framework overhead.</p>
</div>

## Where Latency Usually Comes From

<MermaidDiagram
  caption="API latency is the result of several layers interacting: parsing, service logic, I/O, serialization, pool contention, and sometimes CPU-heavy blocking work."
  chart="flowchart LR; A[Incoming request] --> B[Validation and parsing]; B --> C[Route and service code]; C --> D[DB or external I/O]; D --> E[Serialization]; E --> F[Response]; C --> G[Blocking CPU work]; D --> H[Pool contention];"
/>

## Choosing `async def` Versus `def`

- Use `async def` when the handler directly awaits async I/O.
- Use `def` when the stack is mostly sync and threadpool execution is simpler.
- In both cases, the key question is whether the code path blocks the event loop.

```py
from fastapi import FastAPI
import asyncio
import time

app = FastAPI()


@app.get("/bad")
async def bad_endpoint() -> dict[str, str]:
    time.sleep(0.2)
    return {"status": "blocked"}


@app.get("/better")
async def better_endpoint() -> dict[str, str]:
    await asyncio.to_thread(time.sleep, 0.2)
    return {"status": "offloaded"}
```

<p class="code-caption">`async def` does not make blocking code safe. A sync sleep or CPU-heavy operation still stalls the event loop unless it is moved to a worker thread or another process.</p>

## Validation and Serialization Are Part of the Cost

- Deep response models increase serialization work.
- Returning ORM entities directly couples lazy loading to response generation.
- Narrower DTOs often reduce both latency and accidental I/O.
- Boundary-specific strictness can avoid unnecessary coercion work.

## Database Access Usually Dominates

### Look here first

- query count
- N+1 behavior
- loader options such as `selectinload()` or `joinedload()`
- pool wait time
- transaction length

### Common failure modes

- repeated queries inside routes
- lazy loading during serialization
- waiting for slow external I/O inside a long transaction

## Think About the Worker Model Explicitly

| Layer | Question | Common mistake |
| --- | --- | --- |
| Uvicorn workers | Does worker count fit CPU and memory? | increasing workers blindly |
| DB pool | Does pool sizing match worker concurrency? | many workers, tiny pool |
| request timeout | How are slow downstreams cut off? | waiting forever |
| background jobs | Should work leave the API process entirely? | doing long-running work inline |

## Operational Defaults Worth Adding Early

- separate access logs from application logs
- request or trace IDs
- DB query latency measurements
- timeout, retry, and circuit-breaking policies
- health and readiness endpoints
- checks that response contracts match OpenAPI assumptions

## A Good Debugging Order

1. Measure query count and DB latency.
2. Measure external API latency and timeout behavior.
3. Measure payload size and serialization cost.
4. Measure pool and worker contention.
5. Only then worry about framework overhead.

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Remove hidden blocking</h3>
    <p>Audit `async` code paths for sync I/O and CPU-heavy work that still blocks the loop.</p>
  </div>
  <div class="check-card">
    <h3>Keep response models narrow</h3>
    <p>Return only the fields you need so serialization stays predictable and lazy loading does not leak across the boundary.</p>
  </div>
  <div class="check-card">
    <h3>Tune pools and workers together</h3>
    <p>Application worker count and DB pool size are coupled system settings, not isolated knobs.</p>
  </div>
  <div class="check-card">
    <h3>Do not tune blind</h3>
    <p>Without latency, error-rate, and query metrics, performance work becomes guesswork.</p>
  </div>
</div>

## Official References

- [FastAPI Concurrency and async / await](https://fastapi.tiangolo.com/async/)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/)
- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
