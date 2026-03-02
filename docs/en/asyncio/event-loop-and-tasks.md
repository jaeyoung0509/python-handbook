# Event Loop and Tasks

<p class="lead">`async/await` is a scheduling contract, not just syntax sugar. A coroutine object is a plan for computation, while a task is a unit of work actually scheduled by the event loop. Mixing those concepts leads quickly to task leaks, bad `create_task()` usage, and hidden blocking code.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a coroutine is not running yet; a task is. The event loop can only switch tasks at suspension points such as `await`, so one blocking call can freeze the whole async system.</p>
</div>

## Start With the Scheduling Picture

<MermaidDiagram
  caption="A coroutine object does not execute by itself. It must be awaited or wrapped into a task so the event loop can schedule it."
  chart="flowchart LR; A[async def call] --> B[coroutine object]; B --> C[await in parent task]; B --> D[create_task]; C --> E[event loop schedules work]; D --> E; E --> F[await suspension points]; F --> E;"
/>

## Why It Matters

- It tells you when `create_task()` is safe and when it starts ownership problems.
- It explains why one sync blocking call stalls the event loop.
- It clarifies why async FastAPI endpoints can still behave badly if the internals are blocking.

## A Small Example

```py
import asyncio
import time


def blocking_lookup() -> str:
    time.sleep(0.2)
    return "done"


async def child(name: str) -> str:
    await asyncio.sleep(0.1)
    return f"{name}-ok"


async def main() -> None:
    coro = child("plain")
    task = asyncio.create_task(child("scheduled"))

    print("coro type:", type(coro).__name__)
    print("task type:", type(task).__name__)

    result = await asyncio.to_thread(blocking_lookup)
    print("thread result:", result)
    print("task result:", await task)
    print("coro result:", await coro)


asyncio.run(main())
```

<p class="code-caption">`child("plain")` is only a coroutine object until it is awaited. `create_task()` schedules work immediately. Blocking sync code belongs in `to_thread()` or another executor strategy if you want the loop to stay responsive.</p>

## Good Uses of `create_task()`

- background work with an explicit lifecycle owner
- fan-out work that you will later await or join explicitly
- top-level orchestration code that needs manual task references

## When `TaskGroup` Is Better

- several tasks share one lifecycle boundary
- one failure should cancel the rest
- you want structured error handling instead of loose background tasks

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Remove blocking calls</h3>
    <p>Do not run sync DB drivers, `time.sleep`, or heavy CPU work directly in the loop.</p>
  </div>
  <div class="check-card">
    <h3>Make task ownership explicit</h3>
    <p>If you create a task, be clear about who awaits it, cancels it, and collects its errors.</p>
  </div>
  <div class="check-card">
    <h3>Know the yield points</h3>
    <p>Async code is only cooperative at suspension points; long CPU loops inside `async def` are still blocking.</p>
  </div>
  <div class="check-card">
    <h3>Use thread offload intentionally</h3>
    <p>`asyncio.to_thread()` is a pragmatic bridge for existing sync code, not an excuse to ignore the blocking boundary.</p>
  </div>
</div>

## Official Sources

- [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- [Runners](https://docs.python.org/3/library/asyncio-runner.html)
