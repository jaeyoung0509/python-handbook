# Context Managers

<p class="lead">Context managers are Python's clearest way to express resource ownership and scope. Files, DB sessions, locks, timeouts, lifespan wiring, and test cleanup can all be modeled with the same enter/exit shape.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: `with` is structured `try/finally`. It is the most Pythonic way to make resource scope, transaction scope, and application lifespan explicit in code.</p>
</div>

## See the Execution Shape

<MermaidDiagram
  caption="A context manager acquires or prepares something on entry and guarantees cleanup on exit, whether the body succeeds or fails."
  chart="flowchart LR; A[enter with block] --> B[__enter__ or async __aenter__]; B --> C[body execution]; C --> D[normal exit or exception]; D --> E[__exit__ or async __aexit__];"
/>

## A Small Class-Based Context Manager

```py
class SessionScope:
    def __enter__(self) -> str:
        print("open resource")
        return "session"

    def __exit__(self, exc_type, exc, tb) -> bool:
        print("close resource")
        return False


with SessionScope() as session:
    print("using", session)
```

## `contextlib` Is Often the Cleaner Tool

```py
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def transaction_scope() -> Iterator[str]:
    print("begin")
    try:
        yield "tx"
        print("commit")
    except Exception:
        print("rollback")
        raise
    finally:
        print("close")


with transaction_scope() as tx:
    print("inside", tx)
```

<p class="code-caption">When the lifecycle is simple, `@contextmanager` is often more readable than a dedicated class. If you need reusable stateful objects, a class-based context manager may fit better.</p>

## Async Context Managers Matter Too

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan_scope() -> AsyncIterator[str]:
    print("startup")
    try:
        yield "app-state"
    finally:
        print("shutdown")
```

## Practical Connections

- database session scope
- FastAPI lifespan wiring
- test fixtures and cleanup behavior

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Make scope explicit</h3>
    <p>If a resource has a clear open/close lifecycle, make that scope visible with `with` or `async with`.</p>
  </div>
  <div class="check-card">
    <h3>Treat exception paths seriously</h3>
    <p>Commit vs rollback, startup vs shutdown, and acquire vs release should all be designed together.</p>
  </div>
  <div class="check-card">
    <h3>Pick class vs helper intentionally</h3>
    <p>Classes fit reusable stateful objects; `contextlib` helpers fit simple lifecycle wrappers.</p>
  </div>
  <div class="check-card">
    <h3>Use async context for async resources</h3>
    <p>Async clients, async DB sessions, and lifespan state should usually be managed with `async with`.</p>
  </div>
</div>

## Official Sources

- [contextlib](https://docs.python.org/3/library/contextlib.html)
- [The with statement](https://docs.python.org/3/reference/compound_stmts.html#the-with-statement)
