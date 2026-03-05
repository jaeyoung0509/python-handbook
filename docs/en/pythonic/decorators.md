# Decorators

<p class="lead">Decorators are the cheapest way to attach new behavior in Python. They are also one of the easiest ways to destroy signatures, metadata, and debuggability if you treat wrappers casually.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a good decorator changes behavior while preserving the function's signature and metadata. `functools.wraps` and `ParamSpec` are close to mandatory defaults for serious decorator work.</p>
</div>

## Where a Decorator Acts

<MermaidDiagram
  caption="A decorator takes a callable or class, returns a new callable or class, and inserts extra behavior around the original contract."
  chart="flowchart LR; A[&quot;original function&quot;] --> B[&quot;decorator&quot;]; B --> C[&quot;wrapper function&quot;]; C --> D[&quot;extra behavior before or after call&quot;]; D --> E[&quot;delegate to original&quot;];"
/>

## Baseline Pattern With `wraps` and `ParamSpec`

```py
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def traced(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            print(f"[{name}] before", func.__name__)
            result = func(*args, **kwargs)
            print(f"[{name}] after", func.__name__)
            return result

        return wrapper

    return decorator


@traced("calc")
def add(x: int, y: int) -> int:
    return x + y


print(add(1, 2))
print(add.__name__)
```

<p class="code-caption">`wraps()` preserves metadata such as `__name__`, `__doc__`, and `__wrapped__`. `ParamSpec` keeps the wrapper aligned with the original call signature at type-check time.</p>

## Function vs Class Decorators

- function decorators wrap or augment call behavior
- class decorators post-process class objects
- class decorators are often a lighter alternative to metaclasses

## Overuse Patterns to Watch

<div class="doc-checklist">
  <div class="check-card">
    <h3>Too much implicit behavior</h3>
    <p>Stacking retry, logging, tracing, auth, and transaction behavior across many decorators quickly hurts debuggability.</p>
  </div>
  <div class="check-card">
    <h3>Metadata loss</h3>
    <p>Without `wraps()`, introspection, documentation, and framework integration can break.</p>
  </div>
  <div class="check-card">
    <h3>Type degradation</h3>
    <p>Using `Callable[..., Any]` everywhere turns decorated code into a type-checking blind spot.</p>
  </div>
  <div class="check-card">
    <h3>Stateful wrappers</h3>
    <p>Long-lived mutable state inside decorators can create concurrency and test-isolation problems.</p>
  </div>
</div>

## Practical Connections

- FastAPI route decorators
- dependency helpers
- logging, tracing, and caching wrappers

## Official Sources

- [functools.wraps](https://docs.python.org/3/library/functools.html#functools.wraps)
- [typing.ParamSpec](https://docs.python.org/3/library/typing.html#typing.ParamSpec)
