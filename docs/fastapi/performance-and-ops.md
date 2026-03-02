# Performance and Ops

<p class="lead">FastAPI가 빠르다는 말은 맞지만, 실제 서비스의 병목은 프레임워크가 아니라 blocking I/O, 비싼 validation/serialization, 잘못된 DB loading, pool 설정, worker 수, 관측성 부재에서 더 자주 나온다. 성능은 endpoint 함수 안 한 줄 최적화보다 시스템 경계를 정리하는 쪽이 훨씬 큰 효과를 낸다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: FastAPI 성능 튜닝은 "async endpoint를 더 많이 쓰기"가 아니라, 숨은 blocking 호출 제거, DTO와 query shape 정리, pool/worker 크기 조정, timeout과 tracing 설정부터 시작해야 한다.</p>
</div>

## 병목이 생기는 위치를 먼저 본다

<MermaidDiagram
  caption="웹 서비스 지연 시간은 프레임워크 한 층에서만 결정되지 않는다. CPU, serialization, DB, 외부 API, worker 모델을 같이 봐야 한다."
  chart="flowchart LR; A[Incoming request] --> B[Validation and parsing]; B --> C[Route and service code]; C --> D[DB or external I/O]; D --> E[Serialization]; E --> F[Response]; C --> G[Blocking CPU work]; D --> H[Pool contention];"
/>

## `async def`와 `def`를 의도적으로 선택하기

- `async def`: 내부에서 await 가능한 I/O를 직접 사용할 때
- `def`: 대부분 sync 라이브러리 호출이고, threadpool로 넘기는 편이 단순할 때
- 무엇이든 중요한 것은 "이 함수 안에 event loop를 막는 코드가 있는가"다

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

<p class="code-caption">`async def` 안에서 `time.sleep()`이나 무거운 CPU 계산을 바로 돌리면 event loop 전체가 멈춘다. async 함수라고 자동으로 논블로킹이 되는 것이 아니라, 내부 호출이 await-friendly한지 확인해야 한다.</p>

## validation과 serialization 비용도 API 비용이다

- 응답 모델이 너무 깊으면 직렬화와 필터링 비용이 커진다.
- ORM 객체를 그대로 반환하면 lazy load와 serialization 비용이 섞인다.
- 큰 payload는 필요한 필드만 담는 response DTO로 줄이는 편이 낫다.
- Pydantic strict/lax 정책을 boundary마다 다르게 잡는 것이 불필요한 coercion 비용을 줄인다.

## DB 접근이 대부분의 성능을 결정한다

### 먼저 볼 것

- query count
- N+1 존재 여부
- `selectinload()` / `joinedload()` 사용 여부
- pool wait time
- transaction 길이

### 자주 하는 실수

- route 안에서 반복 쿼리
- 페이지 하나 직렬화하려고 관계를 lazy load로 여러 번 호출
- long-running transaction 안에서 외부 API까지 기다림

## worker model을 분리해서 생각하기

| 층위 | 질문 | 흔한 실수 |
| --- | --- | --- |
| Uvicorn worker 수 | CPU 코어 수와 메모리를 감안했나 | 감으로 worker를 크게 늘림 |
| DB connection pool | worker 수와 pool 크기가 맞나 | worker 8개인데 pool 5로 고정 |
| request timeout | 느린 downstream을 어떻게 끊나 | 타임아웃 없이 무한 대기 |
| background 작업 | API 프로세스 밖으로 분리할 것인가 | 긴 작업을 endpoint 내부에서 직접 처리 |

## 운영에서 꼭 넣어야 할 기본 장치

- access log와 application log 분리
- request id / trace id
- DB query latency 측정
- timeout, retry, circuit-breaking 정책
- health/readiness endpoint
- OpenAPI docs와 실제 response contract 일치 여부 확인

## 성능 문제를 볼 때 순서

1. DB query 수와 지연 시간부터 본다.
2. 외부 API latency와 timeout을 본다.
3. serialization payload 크기와 response model을 본다.
4. worker/pool contention을 본다.
5. 그 다음에 framework overhead를 본다.

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>숨은 blocking 제거</h3>
    <p>`async def` 내부에 sync I/O와 CPU-heavy 작업이 섞여 있지 않은지 먼저 확인한다.</p>
  </div>
  <div class="check-card">
    <h3>응답 모델 최소화</h3>
    <p>필요한 필드만 response DTO에 담아 serialization 비용과 lazy load 위험을 함께 줄인다.</p>
  </div>
  <div class="check-card">
    <h3>pool과 worker를 같이 본다</h3>
    <p>애플리케이션 worker 수와 DB pool 크기는 따로 최적화할 수 있는 값이 아니라 함께 맞춰야 하는 시스템 파라미터다.</p>
  </div>
  <div class="check-card">
    <h3>관측성 없이 튜닝하지 않기</h3>
    <p>request time, query latency, error rate, timeout 수치가 없으면 최적화가 아니라 추측이 된다.</p>
  </div>
</div>

## 공식 자료

- [FastAPI Concurrency and async / await](https://fastapi.tiangolo.com/async/)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/)
- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
