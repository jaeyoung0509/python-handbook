# Observability

<p class="lead">서비스 운영에서 관측성은 "로그 몇 줄 더 찍기"가 아니다. 실제로는 trace, error event, structured log, request context를 한 모델로 묶는 설계다. FastAPI 서비스에서 이 부분이 약하면 느린 요청, 숨은 N+1, 외부 API timeout, background task 실패가 각각 다른 도구에 흩어져서 원인 파악이 매우 느려진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 실무에서는 OpenTelemetry를 trace backbone으로 두고, Sentry를 error/performance product로 붙이고, `structlog` 같은 structured logging 도구로 request context를 정리하는 조합이 읽기 좋다. 중요한 것은 라이브러리 선택 자체보다 "앱 시작 시 한 번만 초기화", "샘플링과 PII 정책 분리", "고카디널리티 태그 남용 금지"다.</p>
</div>

## 추천 조합

| 역할 | 추천 도구 | 왜 쓰나 |
| --- | --- | --- |
| 분산 trace / span | OpenTelemetry | vendor-neutral 기반, FastAPI/SQLAlchemy 계측 생태계가 좋다 |
| 오류 수집 / 성능 모니터링 | Sentry | 에러와 트레이스를 운영 UI에서 빠르게 묶어 보기 좋다 |
| 구조화 로그 / request context | structlog | `contextvars` 기반 request id, trace id 연동이 깔끔하다 |

## 큰 그림

<MermaidDiagram
  caption="좋은 관측성은 로그, 트레이스, 에러가 서로 고립되지 않고 request context와 함께 연결되는 구조다."
  chart="flowchart LR; A[Incoming request] --> B[OpenTelemetry server span]; B --> C[Service and DB spans]; B --> D[Structured logs with request context]; C --> E[Sentry error or performance event]; D --> E; E --> F[Searchable operational timeline];"
/>

## OpenTelemetry는 bootstrap에서 한 번만 붙인다

```py
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def configure_observability(app: FastAPI, engine: object) -> None:
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,metrics",
    )
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
    )
```

<p class="code-caption">FastAPI와 SQLAlchemy 계측은 app/engine bootstrap 시점에 한 번만 연결하는 편이 안전하다. 라우트 함수나 dependency 안에서 반복 호출하면 중복 계측이나 예상치 못한 성능 저하가 생길 수 있다.</p>

## Sentry는 샘플링을 먼저 설계해야 한다

```py
import sentry_sdk
from sentry_sdk.types import SamplingContext


def traces_sampler(context: SamplingContext) -> float:
    if context.get("parent_sampled") is not None:
        return float(context["parent_sampled"])

    transaction_context = context.get("transaction_context", {})
    name = str(transaction_context.get("name", ""))
    if name.startswith("GET /health"):
        return 0.0
    if name.startswith("POST /checkout"):
        return 0.5
    return 0.1


sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    traces_sampler=traces_sampler,
    sample_rate=1.0,
)
```

- error event는 기본적으로 더 높게 보존하고,
- trace는 트래픽과 비용을 보고 더 낮게 샘플링하는 편이 흔하다.
- Sentry 공식 문서도 `traces_sample_rate` 또는 `traces_sampler`를 명시적으로 설계하라고 안내한다.

## `structlog`로 request context를 로그에 묶는다

```py
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars


log = structlog.get_logger()


async def logging_middleware(request, call_next):
    clear_contextvars()
    bind_contextvars(
        request_id=request.headers.get("x-request-id", "generated-id"),
        path=request.url.path,
    )
    response = await call_next(request)
    log.info("request.complete", status_code=response.status_code)
    return response
```

## 좋은 패턴

- request id와 trace id를 같은 request scope에 묶는다.
- health check, metrics, static noise는 tracing 제외를 검토한다.
- span name은 route나 business action 단위로 유지한다.
- DB, 외부 HTTP, queue publish 같은 boundary만 의미 있게 계측한다.
- 에러 수집 전에 PII/secret redaction 기준을 정한다.

## 하지 않는 편이 좋은 것

- 모든 요청을 무조건 100% tracing한다.
- `user_id`, `email`, `order_id` 같은 고카디널리티 값을 metric label이나 span attribute에 남발한다.
- route 안에서 직접 logger/sentry scope를 매번 재초기화한다.
- request body 전체를 로그와 error context에 그대로 실어 보낸다.
- 루프 안 row마다 span을 생성한다.
- OpenTelemetry와 vendor SDK를 중복 자동 계측해서 같은 이벤트를 두 번 보낸다.

## 운영 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>초기화는 한 번</h3>
    <p>instrumentation과 SDK init은 app bootstrap 또는 lifespan setup에서 한 번만 수행한다.</p>
  </div>
  <div class="check-card">
    <h3>샘플링은 계층별로</h3>
    <p>error, trace, profile은 같은 비율로 두지 않고 traffic/비용/중요도에 맞춰 분리한다.</p>
  </div>
  <div class="check-card">
    <h3>고카디널리티 제한</h3>
    <p>metric tag와 span attribute는 검색 가능한 운영 차원 값 위주로 제한한다.</p>
  </div>
  <div class="check-card">
    <h3>PII 정책 선행</h3>
    <p>개인정보와 secret redaction 기준 없이 observability를 넓히면 운영 리스크가 커진다.</p>
  </div>
</div>

## 공식 자료

- [OpenTelemetry Python Getting Started](https://opentelemetry.io/docs/languages/python/getting-started/)
- [OpenTelemetry FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [OpenTelemetry SQLAlchemy Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/sqlalchemy/sqlalchemy.html)
- [Sentry Python Sampling](https://docs.sentry.io/platforms/python/configuration/sampling__v3.x)
- [Sentry Python Tracing Sampling](https://docs.sentry.io/platforms/python/tracing/configure-sampling__v3.x)
- [structlog contextvars](https://www.structlog.org/en/stable/contextvars.html)
