# Memory and GC

## Why It Matters

Python memory behavior is not just "garbage collected." CPython mixes reference counting with cyclic GC, and that affects latency, resource cleanup, and debugging.

## This Chapter Builds

- reference counting
- cyclic GC
- `pymalloc`
- object lifetime
- the direction of incremental cyclic GC in 3.14

## Practical Connections

- large object graphs
- file and socket lifecycle
- memory-leak debugging
