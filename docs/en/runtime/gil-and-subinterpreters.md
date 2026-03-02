# GIL and Subinterpreters

<p class="lead">Most Python concurrency arguments eventually collapse into this topic. Threads, async tasks, processes, subinterpreters, and free-threaded builds are not one-dimensional alternatives; they make different tradeoffs around shared state, isolation, and parallel bytecode execution.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: in traditional CPython, the GIL limits parallel execution of Python bytecode inside one interpreter. Threads can still help I/O-bound workloads, but CPU-bound parallelism usually pushes you toward processes or newer interpreter-level options.</p>
</div>

## Map the Concurrency Choices

<MermaidDiagram
  caption="Python concurrency is a family of choices with different sharing and isolation behavior."
  chart="flowchart LR; A[threading] --> B[shared process state]; C[asyncio] --> B; D[multiprocessing] --> E[separate process state]; F[subinterpreters] --> G[separate interpreter state in one process];"
/>

## What the GIL Actually Restricts

- multiple threads running Python bytecode in parallel inside one interpreter
- many I/O operations and some C extensions can still release the GIL temporarily
- so the useful rule is not "threads are useless," but rather "pure-Python CPU parallelism is limited"

## Why `InterpreterPoolExecutor` Matters

```py
from concurrent.futures import InterpreterPoolExecutor


def square(value: int) -> int:
    return value * value


with InterpreterPoolExecutor(max_workers=2) as pool:
    print(list(pool.map(square, [1, 2, 3, 4])))
```

<p class="code-caption">Subinterpreters give you separate interpreter state within one process. They are more isolated than threads and can be lighter than full processes, but they are not a model for free shared mutable state.</p>

## When Each Tool Fits

| Tool | Good fit | Main caution |
| --- | --- | --- |
| `threading` | I/O-heavy work with shared state | pure-Python CPU scaling is limited |
| `asyncio` | I/O multiplexing and structured concurrency | CPU work still needs offload |
| `multiprocessing` | strong isolation and CPU parallelism | process and IPC overhead |
| subinterpreters | lighter-than-process isolation inside one process | sharing model and library support still matter |

## How to Read Free-Threaded Builds

- they are not the default distribution model today
- ecosystem compatibility and performance tradeoffs still matter
- the important signal is that CPython's concurrency model is evolving

## Practical Connections

- when threads are fine
- when processes are better
- what to expect from `InterpreterPoolExecutor`

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Do you need shared state?</h3>
    <p>Threads are easiest for sharing. Processes and subinterpreters trade sharing for stronger isolation.</p>
  </div>
  <div class="check-card">
    <h3>Is the workload CPU-bound or I/O-bound?</h3>
    <p>This should be your first cut before picking a concurrency strategy.</p>
  </div>
  <div class="check-card">
    <h3>Did you check library compatibility?</h3>
    <p>Especially for subinterpreters and free-threaded builds, third-party library support matters a lot.</p>
  </div>
  <div class="check-card">
    <h3>Did you price the boundary cost?</h3>
    <p>Processes and interpreter boundaries add serialization, communication, and state-management costs.</p>
  </div>
</div>

## Official Sources

- [concurrent.interpreters](https://docs.python.org/3/library/concurrent.interpreters.html)
- [What's New in Python 3.14](https://docs.python.org/3/whatsnew/3.14.html)
- [PEP 703](https://peps.python.org/pep-0703/)
