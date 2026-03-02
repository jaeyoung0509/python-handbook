# CPython vs Go Runtime

## Quick Comparison

| Topic | CPython | Go |
| --- | --- | --- |
| Core execution model | Bytecode interpreter on frames and Python objects | Native code compiled from Go source |
| Memory ownership | Reference counting plus cyclic GC | Tracing garbage collector |
| Concurrency baseline | Threads, processes, coroutines, subinterpreters | Goroutines and channels |
| Shared-state constraint | Traditional builds have a process-wide GIL | No GIL; runtime scheduler coordinates goroutines |
| Introspection | Very rich runtime reflection and dynamic hooks | Simpler runtime model, stronger compile-time assumptions |

## Why This Comparison Helps

- It explains why Python frameworks lean hard on descriptors, annotations, decorators, and import-time metaprogramming.
- It explains why Go code tends to push more work into compile-time structure and explicit interfaces.
- It helps you reason about performance tradeoffs without turning either language into a caricature.

## Where Python Wins

- Runtime introspection and metaprogramming are much richer.
- Framework authors can consume annotations and class bodies directly.
- Dynamic object models make DSL-style APIs easier to build.

## Where Go Wins

- Native-code execution and goroutine scheduling create a simpler performance story for many services.
- Static binaries and a smaller runtime surface reduce operational surprises.
- The memory model and concurrency story are stricter and easier to reason about at scale.

## Read Next

1. [Execution Model](/en/runtime/execution-model)
2. [Memory and GC](/en/runtime/memory-and-gc)
3. [GIL and Subinterpreters](/en/runtime/gil-and-subinterpreters)
