# Testing and Debugging

<p class="lead">Async bugs are often timing bugs, which means they do not always reproduce the same way twice. That is why async testing needs timeout guards, task-leak checks, and debug mode rather than only happy-path assertions.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: do not just assert the final value. Use timeout guards to fail hangs, enable debug mode to surface misuse, and check that no extra tasks survive when the test is done.</p>
</div>

## Debugging Flow

<MermaidDiagram
  caption="Async debugging is about observability: force bounded execution time, enable debug mode, inspect tasks, then fix cleanup or blocking paths."
  chart="flowchart LR; A[Test or local repro] --> B[timeout guard]; B --> C[debug mode]; C --> D[inspect pending tasks]; D --> E[fix cleanup, cancellation, blocking path];"
/>

## First Guardrail to Add

```py
import asyncio


async def fetch_with_guard() -> str:
    async with asyncio.timeout(0.5):
        await asyncio.sleep(0.1)
        return "ok"


def main() -> None:
    runner = asyncio.Runner(debug=True)
    with runner:
        print(runner.run(fetch_with_guard()))


if __name__ == "__main__":
    main()
```

<p class="code-caption">`asyncio.timeout()` turns hangs into failures, while `Runner(debug=True)` or `asyncio.run(..., debug=True)` enables additional debug checks and warnings.</p>

## Simple Task-Leak Check

```py
import asyncio


async def assert_no_extra_tasks() -> None:
    current = asyncio.current_task()
    leaked = {
        task
        for task in asyncio.all_tasks()
        if task is not current and not task.done()
    }
    if leaked:
        raise AssertionError(f"leaked tasks: {leaked}")
```

## What Debug Mode Helps Surface

- forgotten awaits
- wrong thread usage of loop APIs
- slow callbacks and selector operations
- unclosed transports or resource warnings

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Every test gets a timeout</h3>
    <p>Hangs are worse than ordinary failures. Always bound execution time.</p>
  </div>
  <div class="check-card">
    <h3>Verify cleanup paths</h3>
    <p>Cancellation should leave queues, semaphores, and background tasks in a clean state.</p>
  </div>
  <div class="check-card">
    <h3>Use debug mode intentionally</h3>
    <p>Debug mode is excellent for local reproduction and CI diagnosis of subtle async issues.</p>
  </div>
  <div class="check-card">
    <h3>Inspect pending tasks</h3>
    <p>Checking for leftover tasks catches leaks early.</p>
  </div>
</div>

## Official Sources

- [Developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html)
- [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
