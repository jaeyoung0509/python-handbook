# Cancellation and TaskGroup

<p class="lead">The quality of async code is shaped less by how much it can run concurrently and more by how well it handles cancellation and cleanup. `CancelledError` is part of control flow, and `TaskGroup` gives that control flow a structured home.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: cancellation is modeled through exception propagation. If cleanup is required, perform it in `finally` or under `except asyncio.CancelledError`, then usually re-raise. For groups of tasks, `TaskGroup` is the safest default.</p>
</div>

## Picture the Structured-Concurrency Flow

<MermaidDiagram
  caption="When a timeout or child-task failure happens, TaskGroup cancels sibling tasks, lets them clean up, and then reports remaining errors structurally."
  chart="flowchart LR; A[Parent task] --> B[TaskGroup]; B --> C[child task A]; B --> D[child task B]; C --> E[failure or timeout]; E --> F[cancel siblings]; F --> G[cleanup in finally]; G --> H[ExceptionGroup or normal exit];"
/>

## Code Pattern for Proper Cancellation

```py
import asyncio


async def worker(name: str) -> None:
    try:
        while True:
            print(f"{name}: tick")
            await asyncio.sleep(0.2)
    except asyncio.CancelledError:
        print(f"{name}: cleanup")
        raise


async def main() -> None:
    try:
        async with asyncio.timeout(0.6):
            async with asyncio.TaskGroup() as task_group:
                task_group.create_task(worker("alpha"))
                task_group.create_task(worker("beta"))
    except TimeoutError:
        print("timeout reached")


asyncio.run(main())
```

<p class="code-caption">`asyncio.timeout()` surfaces a `TimeoutError` outside the block, but internally it cancels the running work. Each worker must clean up and re-raise `CancelledError` so structured cancellation continues to behave correctly.</p>

## Why Swallowing `CancelledError` Is Dangerous

- the parent loses the cancellation signal
- graceful shutdown sequencing becomes unreliable
- timeout behavior can turn into hanging behavior

## What `TaskGroup` Gives You

- task lifetime tied to a lexical block
- sibling cancellation on failure
- grouped exceptions through `ExceptionGroup`

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Cleanup in finally</h3>
    <p>Files, sockets, semaphores, and consumers should usually clean up in `finally` blocks.</p>
  </div>
  <div class="check-card">
    <h3>Re-raise cancellation</h3>
    <p>Unless you have a very specific reason, do not swallow `CancelledError`.</p>
  </div>
  <div class="check-card">
    <h3>Prefer TaskGroup</h3>
    <p>For new code, `TaskGroup` is usually safer than scattered `create_task()` calls.</p>
  </div>
  <div class="check-card">
    <h3>Design for timeout</h3>
    <p>Timeout paths are part of the contract, especially in fan-out service calls.</p>
  </div>
</div>

## Official Sources

- [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- [Task Groups](https://docs.python.org/3/library/asyncio-task.html#task-groups)
