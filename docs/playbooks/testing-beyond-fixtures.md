# Testing Beyond Fixtures

<p class="lead">fixture 설계가 테스트의 바닥인 것은 맞지만, 거기서 멈추면 서비스 전체 품질은 잘 올라가지 않는다. 좋은 백엔드 테스트 전략은 "어떤 계층을 어떤 도구로 검증할지"를 나눈다. invariant는 unit test, HTTP contract는 ASGI transport, protocol은 websocket test, 이상한 edge case는 property-based test, 성능 감각은 load/perf smoke로 가져가는 편이 맞다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: fixture는 자원 수명주기를 정리하는 도구다. 그 위에 contract test, property-based test, protocol test, perf smoke를 층으로 쌓아야 한다. "pytest 하나"가 아니라 "어떤 위험을 어떤 테스트가 잡는가"로 설계하는 편이 좋다.</p>
</div>

<MermaidDiagram
  caption="좋은 테스트 포트폴리오는 한 종류의 테스트만 늘리는 것이 아니라, 위험별로 역할을 분리한다."
  chart="flowchart TB; A[&quot;Unit invariants&quot;] --> B[&quot;Contract tests&quot;]; B --> C[&quot;Protocol tests&quot;]; C --> D[&quot;Property-based tests&quot;]; D --> E[&quot;Perf and load smoke&quot;];"
/>

## 1) fixture 다음에 오는 테스트 층을 분리한다

| 테스트 종류 | 질문 | 대표 도구 |
| --- | --- | --- |
| unit test | 이 use case branch와 invariant가 맞는가 | `pytest`, fake UoW |
| contract test | HTTP/JSON 계약이 맞는가 | `httpx.ASGITransport`, `TestClient` |
| protocol test | websocket/event ordering이 맞는가 | `TestClient.websocket_connect()` |
| property-based test | edge case 전반에서 invariant가 유지되는가 | `Hypothesis` |
| perf smoke | 병목이 어디쯤 생기는가 | micro-benchmark, `locust`, profiler |

fixture는 이 층들을 지탱하는 공용 자원 graph를 만드는 역할이지, 테스트 전략 전체 그 자체는 아니다.

## 2) HTTP contract test는 ASGI transport로 더 명시적으로 만들 수 있다

`TestClient`는 편하지만, `httpx.ASGITransport`를 쓰면 "실제 HTTP client가 ASGI app을 때린다"는 구조가 더 잘 보인다.

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

이 패턴은 async client behavior, header handling, JSON contract를 더 명시적으로 다룰 때 좋다.

## 3) property-based test는 "예시 하나"가 아니라 invariant를 검증한다

예를 들어 idempotency key 저장소라면 특정 입력 한 건이 아니라 아래 성질이 중요하다.

- 같은 key + 같은 payload는 한 번만 실행된다.
- 같은 key + 다른 payload는 conflict다.
- 이미 저장된 응답은 재사용된다.

```py
from hypothesis import given, strategies as st


@given(
    key=st.text(min_size=1, max_size=20),
    payload=st.text(min_size=1, max_size=20),
)
def test_same_key_same_payload_is_idempotent(key: str, payload: str) -> None:
    ...
```

property-based test는 "아무 생각 없이 random을 돌린다"가 아니라, 도메인 invariant를 수학적 성질처럼 다루는 접근이다.

## 4) protocol test는 HTTP status보다 순서와 수명주기를 본다

WebSocket, streaming, reconnect는 status code보다 sequence가 중요하다.

- connect 시 첫 메시지가 `server.hello`인가
- invalid token이면 어떤 close code를 주는가
- reconnect 후 `resume_from`이 제대로 적용되는가
- disconnect 시 room cleanup이 되는가

즉, protocol test는 response body보다 event ordering을 검증한다.

## 5) fixture가 잘 되어 있어도 anti-pattern은 남는다

- integration test 하나에 domain branching을 다 몰아넣는다.
- property test가 잡을 일을 example 몇 개만으로 끝낸다.
- `BackgroundTasks`, queue, retry 경로를 전혀 검증하지 않는다.
- WebSocket reconnect를 "브라우저에서 한번 해봤다" 수준으로 끝낸다.

## 6) 성능 테스트는 정확한 질문이 먼저다

성능 테스트도 한 종류가 아니다.

- micro-benchmark: 함수/serializer/query shape 한 조각 비용
- load test: 동시 요청, pool, timeout, backpressure
- soak test: 긴 시간 동안 leak / queue buildup / reconnect churn

중요한 건 benchmark 숫자보다 "무엇을 측정했고, 어떤 병목을 가설로 두었는가"다.

## 7) 추천 테스트 포트폴리오

### service / use case

- fake UoW 기반 unit test
- branch / validation / commit policy 검증

### HTTP API

- `TestClient` 또는 `ASGITransport` contract test
- request/response DTO, status code, error envelope 검증

### realtime / messaging

- websocket protocol test
- reconnect / resume / broadcast ordering 검증

### resilience

- idempotency invariant test
- retry / duplicate delivery / outbox flush test

## 8) 이 저장소에서 같이 보면 좋은 파일

- `tests/test_fastapi_fixtures_and_teardown.py`
- `tests/test_idempotency_and_contracts.py`
- `examples/idempotency_outbox_lab.py`
- [ABC + Fake UoW 테스트](/playbooks/testing-abc-and-fake-uow)

## 공식 자료

- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/)
- [HTTPX transports](https://www.python-httpx.org/advanced/transports/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
