# GIL and Subinterpreters

## Why It Matters

Concurrency decisions in Python only become sane once you distinguish threads, async tasks, processes, per-interpreter state, and the GIL.

## This Chapter Builds

- what the GIL actually restricts
- I/O-bound vs CPU-bound workloads
- per-interpreter GIL work
- free-threaded builds
- the subinterpreter model

## Practical Connections

- when threads are fine
- when processes are better
- what to expect from `InterpreterPoolExecutor`
