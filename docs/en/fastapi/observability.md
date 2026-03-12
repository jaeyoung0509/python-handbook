# Observability

<p class="lead">Observability is not just "more logging." In real services, it is the design that connects traces, error events, structured logs, and request context into one coherent operating model. Without that, slow requests, hidden N+1 queries, downstream timeouts, and background-task failures end up scattered across unrelated tools.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a practical FastAPI stack often uses OpenTelemetry as the trace backbone, Sentry as the error and performance product, and `structlog` for structured request-scoped logs. The important part is not the brand list; it is initializing them once at startup, separating sampling from PII policy, and avoiding high-cardinality spam.</p>
</div>

## A Practical Stack

| Role | Good default | Why |
| --- | --- | --- |
| distributed traces and spans | OpenTelemetry | vendor-neutral foundation with strong FastAPI and SQLAlchemy instrumentation |
| error and performance monitoring | Sentry | useful operational UI for errors plus tracing context |
| structured logs and request context | structlog | clean `contextvars` story for request and trace correlation |

## The Big Picture

<MermaidDiagram
  caption="Good observability connects logs, traces, and errors through one request context instead of leaving them isolated."
  chart="flowchart LR; A[Incoming request] --> B[OpenTelemetry server span]; B --> C[Service and DB spans]; B --> D[Structured logs with request context]; C --> E[Sentry error or performance event]; D --> E; E --> F[Searchable operational timeline];"
/>

## Instrument OpenTelemetry Once During Bootstrap

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

<p class="code-caption">FastAPI and SQLAlchemy instrumentation should usually be attached once during bootstrap. Doing it inside routes or dependencies can cause duplicate instrumentation and confusing runtime behavior.</p>

## Design Sentry Sampling Deliberately

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

- Error retention and trace sampling usually deserve different rates.
- Sentry's docs explicitly recommend deliberate use of `traces_sample_rate` or `traces_sampler`.
- Inherited parent sampling decisions usually should be preserved so distributed traces stay intact.

## Bind Request Context into Logs with `structlog`

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

## Good Patterns

- bind request IDs and trace IDs in one request scope
- exclude health checks and other noisy low-value paths from tracing
- keep span names at route or business-action granularity
- instrument meaningful boundaries such as DB, outbound HTTP, or queue publishing
- decide PII and secret redaction before shipping events broadly

## Patterns to Avoid

- tracing every request at 100% without considering volume
- adding high-cardinality values such as `user_id`, `email`, or `order_id` everywhere
- reinitializing logger or Sentry scope repeatedly inside route handlers
- logging whole request bodies or raw secrets
- creating spans inside tight per-row loops
- double auto-instrumenting the same path with overlapping SDKs

## Operational Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Initialize once</h3>
    <p>Instrumentation and SDK setup should live in app bootstrap or lifespan setup, not inside request handlers.</p>
  </div>
  <div class="check-card">
    <h3>Sample by signal type</h3>
    <p>Error, trace, and profiling signals usually should not all use the same rate.</p>
  </div>
  <div class="check-card">
    <h3>Constrain cardinality</h3>
    <p>Metric tags and span attributes should stay searchable and bounded.</p>
  </div>
  <div class="check-card">
    <h3>Set PII policy first</h3>
    <p>Broad instrumentation without redaction rules creates operational and compliance risk quickly.</p>
  </div>
</div>

## Scenario Table

| symptom | inspect first | likely root cause | safe mitigation | what not to do |
| --- | --- | --- | --- | --- |
| p95 jumps right after a release but traces are patchy | inspect whether instrumentation was duplicated at bootstrap and whether sampling changed | SDKs were reinitialized inside routes or sampling was accidentally reduced | remove duplicate initialization and temporarily raise sampling only for key endpoints | switch the whole service to permanent 100% tracing under pressure |
| 500 alerts fire but logs, errors, and traces cannot be correlated | inspect whether request ID and trace ID are bound in the same request scope | correlation propagation is missing or middleware/contextvars binding broke | restore request-scoped binding and normalize shared correlation fields on hot paths | dump raw request bodies and secrets into logs as a shortcut |
| observability cost spikes and search gets slower | inspect metric tags and span attributes for high-cardinality values | fields such as `user_id`, `email`, or `order_id` were added too broadly | remove high-cardinality fields and keep only bounded searchable dimensions | ignore the cardinality issue and only shorten retention until the signal becomes useless |

## Code Review Lens

- Check whether instrumentation and SDK setup happen once during bootstrap or lifespan.
- Check whether request IDs, trace IDs, and error events share one request context.
- Check whether sampling and redaction policy are explicit instead of hidden inside tool defaults.
- Check whether spans, tags, and log fields stay within bounded cardinality.

## Common Anti-Patterns

- reinitializing logger scope, tracer setup, or Sentry SDK inside routes or dependencies
- having traces without request IDs or logs that never correlate with traces
- storing full request or response bodies in operational logs or error context
- adding more metric labels or span attributes every time something becomes hard to debug

## Likely Discussion Questions

- During an incident, which signal would you inspect first and how would you correlate the rest?
- Why is bootstrap-time instrumentation safer than route-level initialization?
- Which fields belong in traces and logs, and which should be redacted or omitted?
- When tracing cost rises, what should be constrained before you just reduce retention?

## Strong Answer Frame

- Start by checking whether logs, traces, and errors share the same request context.
- Diagnose the system through four separate concerns: initialization point, sampling, cardinality, and redaction.
- Under pressure, increase signal in a bounded way and then restore conservative defaults once the cause is known.
- Close by framing observability as an operational contract, not a pile of vendor SDKs.

## Official References

- [OpenTelemetry Python Getting Started](https://opentelemetry.io/docs/languages/python/getting-started/)
- [OpenTelemetry FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [OpenTelemetry SQLAlchemy Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/sqlalchemy/sqlalchemy.html)
- [Sentry Python Sampling](https://docs.sentry.io/platforms/python/configuration/sampling__v3.x)
- [Sentry Python Tracing Sampling](https://docs.sentry.io/platforms/python/tracing/configure-sampling__v3.x)
- [structlog contextvars](https://www.structlog.org/en/stable/contextvars.html)
