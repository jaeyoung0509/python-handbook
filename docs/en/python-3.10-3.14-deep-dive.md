# Python 3.10~3.14 Deep Dive

## What This Page Is

This English page is a compact map of the longer Korean notes. Use it as a release-history index, then jump into the topic chapters for deeper treatment.

## Three-Minute Summary

- Python 3.10 made control flow and typing ergonomics much nicer: `match`, `X | Y`, `ParamSpec`, `TypeGuard`, `zip(strict=True)`.
- Python 3.11 changed the feel of CPython execution: adaptive specialization, `ExceptionGroup`, `except*`, `TaskGroup`, and better tracebacks.
- Python 3.12 made typing feel more like part of the language: type parameter syntax, `type` aliases, `sys.monitoring`, and comprehension improvements.
- Python 3.13 started exposing the shape of a post-GIL future: experimental free-threaded builds, experimental JIT, clearer `locals()`, generic defaults, and `warnings.deprecated`.
- Python 3.14 pushes more metaprogramming and runtime capabilities into public APIs: deferred annotations by default, `annotationlib`, template strings, multiple interpreters in the stdlib, and incremental cyclic GC work.

## Version Map

| Version | Big idea | Why it matters |
| --- | --- | --- |
| 3.10 | Readable control flow | Pattern matching and typing ergonomics reduce boilerplate in real service code. |
| 3.11 | Faster and better structured execution | Specialization and structured concurrency change performance and async error handling. |
| 3.12 | Typing becomes language-shaped | Generic syntax becomes easier to read and write. |
| 3.13 | CPython experiments become visible | The runtime starts exploring free-threading and JIT more openly. |
| 3.14 | Annotation and interpreter APIs mature | Framework authors get better tools for introspection and isolation. |

## Best Reading Order

1. `match`, `TaskGroup`, and `ExceptionGroup` if you want immediate day-to-day payoff.
2. Type parameter syntax, generic defaults, and deferred annotations if you care about modern typing.
3. Specialization, `sys.monitoring`, free-threaded builds, and interpreter APIs if you care about tools or runtime internals.

## Related Chapters

- [Modern Typing](/en/typing/modern-typing)
- [Runtime vs Static](/en/typing/runtime-vs-static)
- [Bytecode and Specialization](/en/runtime/bytecode-and-specialization)
- [GIL and Subinterpreters](/en/runtime/gil-and-subinterpreters)

## Official Sources

- [What's New in Python 3.10](https://docs.python.org/3/whatsnew/3.10.html)
- [What's New in Python 3.11](https://docs.python.org/3/whatsnew/3.11.html)
- [What's New in Python 3.12](https://docs.python.org/3/whatsnew/3.12.html)
- [What's New in Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)
- [What's New in Python 3.14](https://docs.python.org/3/whatsnew/3.14.html)
