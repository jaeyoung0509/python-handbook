# Testing Beyond Fixtures

<p class="lead">Fixture design is the foundation, but stopping there leaves a lot of risk uncovered. Strong backend testing means choosing the right test style for each failure mode. Invariants belong in unit tests, HTTP boundaries fit contract tests, protocol behavior needs websocket tests, strange edge cases fit property-based tests, and performance intuition comes from load or profiling work.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: fixtures organize resource lifecycles. On top of that you should layer contract tests, property-based tests, protocol tests, and performance smoke. Do not think in terms of "just pytest". Think in terms of "which risk does this test catch?".</p>
</div>

<MermaidDiagram
  caption="A strong test portfolio separates test roles by risk instead of scaling only one test style."
  chart="flowchart TB; A[&quot;Unit invariants&quot;] --> B[&quot;Contract tests&quot;]; B --> C[&quot;Protocol tests&quot;]; C --> D[&quot;Property-based tests&quot;]; D --> E[&quot;Perf and load smoke&quot;];"
/>

## 1) Split the testing layers after fixtures

| Test type | Main question | Typical tools |
| --- | --- | --- |
| unit test | is the use-case branch or invariant correct? | `pytest`, fake UoW |
| contract test | does the HTTP/JSON contract hold? | `httpx.ASGITransport`, `TestClient` |
| protocol test | does websocket or event ordering hold? | `TestClient.websocket_connect()` |
| property-based test | does the invariant survive broad edge cases? | `Hypothesis` |
| perf smoke | where does pressure appear first? | micro-benchmarks, `locust`, profilers |

Fixtures support these layers by managing shared resource lifecycles. They are not the full strategy by themselves.

## 2) HTTP contract tests can be clearer with ASGI transport

`TestClient` is convenient, but `httpx.ASGITransport` makes the "an HTTP client is calling an ASGI app" structure very explicit.

```py
import asyncio

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def run_contract() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.json() == {"status": "ok"}


asyncio.run(run_contract())
```

This style is useful when you want an explicit async client path, transport behavior, or header-level contract coverage.

## 3) Property-based tests verify invariants, not only examples

Consider an idempotency-key store. The important properties are not one or two example cases but rules such as:

- same key plus same payload executes once
- same key plus different payload conflicts
- a stored response is reused

```py
from hypothesis import given, strategies as st


@given(
    key=st.text(min_size=1, max_size=20),
    payload=st.text(min_size=1, max_size=20),
)
def test_same_key_same_payload_is_idempotent(key: str, payload: str) -> None:
    ...
```

Property-based tests are not "random testing". They are a way to express domain invariants as broad executable properties.

## 4) Protocol tests care about sequence and lifetime

For WebSockets, streaming, and reconnect flows, status codes are not enough.

- does connect produce the expected `server.hello` frame?
- what close code is used for an invalid token?
- does `resume_from` work correctly after reconnect?
- is room cleanup triggered on disconnect?

Protocol tests validate event ordering and lifecycle rules, not only response payloads.

## 5) Common anti-patterns that survive even with good fixtures

- pushing all domain branching into slow integration tests
- relying only on a few examples when a property test would describe the invariant better
- never testing `BackgroundTasks`, queue, or retry paths
- treating WebSocket reconnect as "it worked once in the browser"

## 6) Performance testing needs a precise question first

Performance testing is not one thing.

- micro-benchmark: one function, serializer, or query shape
- load test: concurrency, pools, timeouts, backpressure
- soak test: long-term leaks, queue buildup, reconnect churn

The important artifact is not the raw number. It is the question being asked and the bottleneck hypothesis being tested.

## 7) Recommended test portfolio

### service / use case

- fake-UoW unit tests
- branch, validation, and commit-policy checks

### HTTP API

- `TestClient` or `ASGITransport` contract tests
- request DTO, response DTO, status code, and error envelope checks

### realtime / messaging

- websocket protocol tests
- reconnect, resume, and broadcast-order checks

### resilience

- idempotency invariant tests
- retry, duplicate-delivery, and outbox-flush tests

## 8) Good companion files in this repository

- `tests/test_fastapi_fixtures_and_teardown.py`
- `tests/test_idempotency_and_contracts.py`
- `examples/idempotency_outbox_lab.py`
- [ABC + Fake UoW Testing](/en/playbooks/testing-abc-and-fake-uow)

## Official References

- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/)
- [HTTPX transports](https://www.python-httpx.org/advanced/transports/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
