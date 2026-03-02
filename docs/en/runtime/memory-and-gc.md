# Memory and GC

<p class="lead">Python memory behavior is different from tracing-GC languages such as Go or Java because CPython combines reference counting with cyclic garbage collection. Many objects disappear immediately, but cycles need a separate collection step.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: CPython memory is best understood as "immediate cleanup from reference counting, plus separate cycle detection." That makes resource lifetime more predictable in some cases, but large cyclic graphs and pause behavior still matter.</p>
</div>

## Memory-Reclamation Flow

<MermaidDiagram
  caption="Most objects disappear when their reference count reaches zero. Cycles survive that step and need cyclic GC to reclaim them."
  chart="flowchart LR; A[object created] --> B[reference count changes]; B --> C{refcount == 0?}; C -->|yes| D[immediate deallocation]; C -->|no| E[possible cycle survives]; E --> F[cyclic GC scan]; F --> G[cycle reclaimed];"
/>

## Small Cycle Example

```py
import gc


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.other: Node | None = None


left = Node("left")
right = Node("right")
left.other = right
right.other = left

del left
del right

print("collected objects:", gc.collect())
```

<p class="code-caption">The two nodes keep each other alive through a reference cycle. Reference counting alone cannot reclaim them once the external references disappear.</p>

## `pymalloc` Intuition

- CPython uses a specialized allocator for many small objects.
- "This object was freed" is not the same as "memory was returned to the OS immediately."
- That is why process RSS does not always fall as quickly as you might expect.

## The 3.14 Direction

- cyclic-GC work is moving toward smaller incremental steps
- the goal is lower pause impact for latency-sensitive workloads
- memory-management evolution is tied to the broader runtime changes around concurrency

## Practical Connections

- large object graphs
- file and socket lifecycle
- memory-leak debugging

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Do not rely on GC for resource cleanup</h3>
    <p>Files, sockets, and sessions should usually be closed explicitly or through context managers.</p>
  </div>
  <div class="check-card">
    <h3>Watch for cycles</h3>
    <p>Graphs, listeners, and back-references are common sources of cyclic retention.</p>
  </div>
  <div class="check-card">
    <h3>Do not read RSS alone</h3>
    <p>Allocator behavior means stable RSS is not automatically a memory leak.</p>
  </div>
  <div class="check-card">
    <h3>Use the right tools</h3>
    <p>`gc`, tracemalloc, and object-graph inspection together are much more informative than one metric alone.</p>
  </div>
</div>

## Official Sources

- [gc](https://docs.python.org/3/library/gc.html)
- [Garbage collector design](https://github.com/python/cpython/blob/main/InternalDocs/garbage_collector.md)
