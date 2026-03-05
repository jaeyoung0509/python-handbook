# CPython Internals Advanced

<p class="lead">This chapter treats CPython internals as an execution model, not as trivia. Once you connect source -> AST -> code object -> frame -> eval loop -> object/memory layers, performance discussions become concrete instead of vague.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: build intuition in three layers: execution (frame/code/bytecode), object model (`PyObject`, type, refcount), and memory model (refcount plus cyclic GC plus allocators). Then verify with `dis`, `ast`, `gc`, `tracemalloc`, and `sys.monitoring` labs.</p>
</div>

## Execution Pipeline

<MermaidDiagram
  caption="Python source moves through multiple internal stages before object-level operations execute."
  chart="flowchart LR; A[&quot;Source code&quot;] --> B[&quot;AST&quot;]; B --> C[&quot;Code object&quot;]; C --> D[&quot;Frame object&quot;]; D --> E[&quot;Bytecode eval loop&quot;]; E --> F[&quot;PyObject operations&quot;];"
/>

## 1) Keep code objects and frames distinct

- code object: static execution plan (constants, names, bytecode)
- frame object: runtime context (locals, stack, current instruction)
- one function object can produce many frames across calls

```py
import inspect


def sample(x: int, y: int) -> int:
    frame = inspect.currentframe()
    assert frame is not None
    print("frame locals keys:", list(frame.f_locals))
    return x + y
```

## 2) Bytecode specialization helps stable hot paths

- in Python 3.11+, adaptive specialization optimizes common opcode paths
- highly polymorphic paths can reduce specialization benefit
- `dis.dis()` is the fastest way to inspect execution shape

```py
import dis


def add_loop(n: int) -> int:
    total = 0
    for i in range(n):
        total += i
    return total


dis.dis(add_loop)
```

## 3) Memory model: refcount plus cyclic GC

<MermaidDiagram
  caption="CPython combines immediate deallocation from reference counting with periodic cycle collection."
  chart="flowchart LR; A[&quot;Object refcount reaches 0&quot;] --> B[&quot;Immediate deallocation&quot;]; C[&quot;Reference cycle remains&quot;] --> D[&quot;Generational GC scan&quot;]; D --> E[&quot;Cycle collected&quot;];"
/>

- many objects are deallocated immediately when refcount hits zero
- cyclic references survive refcount and need GC collection
- `__del__` can complicate finalization order and timing

## 4) Use observability tools intentionally

| Tool | Purpose | Typical use |
| --- | --- | --- |
| `dis` | inspect bytecode | compare execution shape |
| `ast` | inspect syntax trees | code analysis/generation |
| `gc` | inspect collector state | cycle and tuning investigations |
| `tracemalloc` | trace allocations | leak and growth investigation |
| `sys.monitoring` | low-overhead runtime events | event-level execution labs |

## 5) Read GIL, free-threaded builds, and subinterpreters on one axis

- default CPython: GIL constrains parallel bytecode execution
- free-threaded build variants: different parallelism tradeoffs
- subinterpreters: isolation-oriented parallelism tradeoff

The key question is not "which is always faster?" but "which sharing and isolation costs fit this workload?"

## Suggested Lab Routine

1. compare two functions with `dis`
2. inspect top allocation lines with `tracemalloc`
3. create a reference cycle and inspect `gc.collect()`
4. collect a small event sample with `sys.monitoring` when available

This repository includes `examples/cpython_runtime_labs.py` for these steps.

## Common Mistakes

- treating refcount and GC as the same mechanism
- generalizing full-system conclusions from tiny micro-benchmarks
- assuming one bytecode detail explains all latency
- ignoring framework I/O and DB costs while over-focusing on interpreter internals

## Good Companion Chapters

- [Execution Model](/en/runtime/execution-model)
- [Memory and GC](/en/runtime/memory-and-gc)
- [Bytecode and Specialization](/en/runtime/bytecode-and-specialization)
- [CPython vs Go Runtime](/en/cpython-vs-go-runtime)

## Official References

- [dis](https://docs.python.org/3/library/dis.html)
- [ast](https://docs.python.org/3/library/ast.html)
- [gc](https://docs.python.org/3/library/gc.html)
- [tracemalloc](https://docs.python.org/3/library/tracemalloc.html)
- [sys.monitoring](https://docs.python.org/3/library/sys.monitoring.html)
- [CPython Developer Guide](https://devguide.python.org/internals/interpreter/)
