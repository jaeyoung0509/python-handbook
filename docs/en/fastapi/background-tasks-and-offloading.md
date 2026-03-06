# Background Tasks and Offloading

<p class="lead">FastAPI's `BackgroundTasks` is convenient, but the name makes it easy to confuse with a durable worker queue. It is much narrower than that. In practice it means "small follow-up work in the same process after the response". If that boundary is unclear, teams either wrap blocking calls in fake async code or push critical work into memory with no durability story.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: if the work affects the response or transaction outcome, do it inline and wait for it. If it is short best-effort follow-up work, `BackgroundTasks` is fine. If it is retry-worthy, durable, CPU-heavy, or long-running, move it to a queue and worker model. The choice between `def` and `async def` inside `BackgroundTasks` depends on whether the actual work is sync I/O or awaitable I/O.</p>
</div>

## Start with the decision shape

<MermaidDiagram
  caption="The real choice is about ownership and failure semantics, not about using async syntax everywhere."
  chart="flowchart TB; A[&quot;Does the work affect the response result&quot;] -->|Yes| B[&quot;Call or await it inline in route or service&quot;]; A -->|No| C[&quot;Is it short in-process best-effort work&quot;]; C -->|Yes, sync I/O| D[&quot;BackgroundTasks plus def&quot;]; C -->|Yes, async I/O| E[&quot;BackgroundTasks plus async def&quot;]; C -->|No| F[&quot;Queue and worker&quot;];"
/>

## What `BackgroundTasks` really means

- It is response-attached follow-up work.
- It runs in the same process.
- It is not a durable queue.
- If the process dies, the task may disappear.
- Tasks run in order, and if one task raises, later tasks do not run.

That means requirements like "the email must eventually be sent", "an invoice must always be generated after payment", or "the task needs retries" do not belong in `BackgroundTasks` alone.

## Choosing `def` vs `async def`

### `BackgroundTasks` plus `def`

Good fit:

- short sync I/O
- file append, audit log write, small JSON dump
- a library that only exposes sync APIs

Why it is acceptable:

- Starlette can run sync background tasks in a thread pool.
- You do not have to turn the whole code path into async just to schedule small follow-up work.

Watch out for:

- CPU-heavy work does not belong here.
- Thread pool tokens are limited.
- Do not pass request-scoped resources like DB sessions directly into the task.

### `BackgroundTasks` plus `async def`

Good fit:

- the task body is fully awaitable I/O
- `httpx.AsyncClient`, async Redis clients, async broker publishers, and similar paths

Why it fits:

- no unnecessary thread hop if the rest of the stack is already async
- easier timeout and backpressure handling in the event-loop model

Watch out for:

- `async def` is not automatically safe
- putting `time.sleep()`, sync SDK calls, or heavy CPU work inside it will still block the event loop

## A practical decision table

| Question | If yes | Recommended path |
| --- | --- | --- |
| Does the result affect the response status or body? | yes | do not push it to background; wait for it inline |
| Does failure require retry or delivery guarantees? | yes | use a queue and worker |
| Is it CPU-heavy? | yes | use a queue, worker, or separate compute path |
| Is it short sync I/O? | yes | `BackgroundTasks` plus `def` |
| Is it short async I/O? | yes | `BackgroundTasks` plus `async def` |

## Why you should not pass request-scoped resources through

FastAPI `yield` dependencies are cleaned up after the response boundary. The current FastAPI guidance is not to rely on reusing those resources from background tasks. That means background tasks should receive identifiers or payloads, then open their own resources if needed.

### Fragile shape

```py
async def create_user(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    user = UserRecord(email="neo@example.com")
    session.add(user)
    await session.commit()

    background_tasks.add_task(send_welcome_email, session, user.id)
    return {"status": "ok"}
```

### Safer shape

```py
async def create_user(
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    user_id = 1
    background_tasks.add_task(send_welcome_email, user_id)
    return {"status": "ok"}
```

```py
async def send_welcome_email(user_id: int) -> None:
    async with AsyncSessionFactory() as session:
        user = await session.get(UserRecord, user_id)
        ...
```

## Example tasks and recommended placement

| Task | Best place | Why |
| --- | --- | --- |
| payment authorization | inline in route or service | directly affects response and consistency |
| one audit log line | `BackgroundTasks` plus `def` | short and best-effort |
| async webhook notification | `BackgroundTasks` plus `async def` | awaitable I/O after the response |
| PDF rendering, image resize | queue and worker | CPU-heavy and often retry-worthy |
| must-deliver email | queue and worker | durability and retries matter |

## Common mistakes

- pushing important work into background just to return faster
- keeping blocking sync SDK calls inside `async def`
- passing request-scoped DB sessions into background tasks
- assuming `BackgroundTasks` behaves like a durable retry queue

## Companion chapters

1. [ASGI and Uvicorn](/en/fastapi/asgi-and-uvicorn)
2. [Lifespan and Testing](/en/fastapi/lifespan-and-testing)
3. [Asyncio](/en/asyncio/)

For runnable examples, pair this chapter with `examples/fastapi_background_tasks_patterns.py`.

## Official References

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI Dependencies with `yield`](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
- [Starlette Background Tasks](https://www.starlette.io/background/)
- [Starlette Thread Pool](https://www.starlette.io/threadpool/)
