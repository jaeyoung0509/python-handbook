# Deployment and Engine Settings

<p class="lead">SQLAlchemy settings are not a bag of magical numbers. Lambda, Kubernetes, batch workers, and long-lived API servers have different process lifetimes, different connection budgets, and different shutdown behavior. Copy-pasting one `engine` and `pool` configuration across all of them is how connection incidents start.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: first calculate process lifetime, concurrency shape, and whether you already have an external pooler. Only then should you decide between `QueuePool` and `NullPool`, and only then should you pick `pool_size` and `max_overflow`.</p>
</div>

## Three Questions to Answer First

1. Is the process long-lived, or does it end per invocation or job?
2. How many processes, workers, or replicas can be alive at the same time?
3. Is there already an external pooler such as RDS Proxy or PgBouncer?

## Calculate Connection Budget Up Front

```text
upper bound of DB connections ~= replicas * workers_per_pod * (pool_size + max_overflow)
```

<p class="code-caption">This matters most for long-lived API servers. Six replicas, two workers each, and `pool_size=10` plus `max_overflow=10` can already imply 240 connections. If you never do this math, the database hits the limit before the app team realizes why.</p>

## What the Important Settings Really Control

| Setting | What it changes | When it usually matters |
| --- | --- | --- |
| `poolclass` | the pool strategy itself | choosing `QueuePool` vs `NullPool` |
| `pool_size` | steady-state kept connections | long-lived API servers |
| `max_overflow` | temporary burst connections above the pool | bursty API traffic |
| `pool_timeout` | how long checkout waits for a connection | detecting saturation quickly |
| `pool_pre_ping` | validates a connection on checkout | environments with idle disconnects |
| `pool_recycle` | recreates older connections | databases with idle timeouts |
| `pool_use_lifo` | prefers the most recently used connections | reducing hot idle connections |
| `autoflush=False` | reduces implicit flushes | service-oriented repository boundaries |
| `expire_on_commit=False` | makes post-commit access less surprising | API DTO assembly and logging |
| `echo` | SQL logging | local debugging only |

## Recommended Profiles by Deployment Target

| Target | Recommended pool | Session scope | Main point |
| --- | --- | --- | --- |
| Lambda with direct DB access | `NullPool` | one session per invocation | concurrency fans out across execution environments, not one shared app process |
| Lambda with RDS Proxy or PgBouncer | `NullPool` or a tiny pool | one session per invocation | if an external pooler already exists, keep app-side pooling small |
| Kubernetes sync API | `QueuePool` | one session per request | choose `pool_size` and `max_overflow` from the connection budget |
| Kubernetes async API | async engine with a bounded pool | one `AsyncSession` per request | never share one `AsyncSession` across concurrent tasks |
| batch, CLI, worker | `NullPool` or a tiny pool | one session per job | large app-side pools often do not help short-lived jobs |

## Guidance for Lambda

### Why `NullPool` often comes first

- Lambda work is short-lived per invocation.
- Rising concurrency creates more execution environments, not a bigger in-process worker pool.
- In practice, a short session per invocation is often easier to reason about than a large app-side pool.

### Baseline example

```py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def handler(event, context):
    session = SessionFactory()
    try:
        ...
    finally:
        session.close()
```

<p class="code-caption">For Lambda, initialize the engine outside the handler so the execution environment can reuse it, but create a fresh session for each invocation. AWS explicitly recommends initializing SDK clients and database connections outside the handler to benefit from environment reuse.</p>

### Lambda with RDS Proxy

- Once RDS Proxy or PgBouncer is in front of the database, large app-side pools become less useful.
- Start with `NullPool` or a very small application-side pool.
- Avoid "double pooling" that hides the real connection math.

## Guidance for Kubernetes

FastAPI's deployment guidance recommends keeping containers simple, and in Kubernetes that often means one Uvicorn process per container. That also makes the database connection budget easier to reason about.

### Baseline sync API example

```py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_timeout=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_use_lifo=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)
```

### Why these values show up often

- `pool_pre_ping=True`: catches stale idle connections early in the request path
- `pool_recycle=1800`: rebuilds connections before common server-side idle timeouts
- `pool_timeout=5`: fails fast instead of waiting forever under saturation
- `pool_use_lifo=True`: favors recently used connections and can reduce unnecessary hot-idle churn

### Worker count changes the math

- one worker per pod keeps the connection story simple
- four workers per pod means four independent engine pools
- always calculate `replicas * workers * (pool_size + max_overflow)` first

## Guidance for Async Services

```py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_timeout=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_use_lifo=True,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)
```

- async does not make session-sharing safe
- create one `AsyncSession` per request or work unit
- call `await engine.dispose()` during shutdown so cleanup is explicit

## Guidance for Batch Jobs and Workers

- short-lived jobs are usually simpler with `NullPool`
- even long-running workers rarely need a large pool unless they truly sustain parallel DB pressure
- calling `engine.dispose()` at the end keeps ownership explicit

## Patterns to Avoid

- using the exact same pool settings for Lambda and Kubernetes
- configuring a large application pool on top of RDS Proxy or PgBouncer
- setting high `max_overflow` values without connection-budget math
- holding sessions beyond request or job scope
- sharing one `AsyncSession` across concurrent tasks
- leaving `echo=True` on in production

## Runnable Example in This Repository

Recommended deployment profiles are summarized in `examples/sqlalchemy_deployment_profiles.py`.

## Good Companion Chapters

- [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
- [Async SQLAlchemy](/en/sqlalchemy/async-sqlalchemy)
- [Performance and Ops](/en/fastapi/performance-and-ops)

## Official References

- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Using AWS Lambda with Amazon RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/)
