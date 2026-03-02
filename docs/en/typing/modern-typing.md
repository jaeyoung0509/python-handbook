# Modern Typing

<p class="lead">In many Python teams, typing is now a baseline assumption. Since Python 3.10, the syntax has become much more readable, which means typing is no longer just extra ceremony; it can actively improve API clarity.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: modern typing is about readable primitives such as `X | Y`, `type` aliases, `Annotated`, `Literal`, `Self`, `Never`, and built-in generic syntax. These tools make API shape easier to express directly in code.</p>
</div>

## Quick Map of the Syntax

| Feature | Why it matters | Example |
| --- | --- | --- |
| `X | Y` | Much cleaner than `Union[X, Y]` | `str | None` |
| `type` aliases | Makes alias intent explicit | `type UserId = int` |
| `Annotated` | Carries type plus metadata | `Annotated[int, Query(gt=0)]` |
| `Literal` | Constrains allowed values | `Literal["draft", "published"]` |
| `Self` | Improves fluent and class-return APIs | `def publish(self) -> Self` |
| `Never` | Marks impossible return paths | `def fail() -> Never` |
| built-in generics | Keeps syntax native | `dict[str, int]` |

## Practical Example

```py
from typing import Annotated, Literal, Never, Self


type UserId = int
type Status = Literal["draft", "published"]


class Article:
    def __init__(self, title: str, status: Status = "draft") -> None:
        self.title = title
        self.status = status

    def publish(self) -> Self:
        self.status = "published"
        return self


def fail(message: str) -> Never:
    raise RuntimeError(message)


PageSize = Annotated[int, "1..100 constraint lives here"]
```

## Why `Annotated` Matters

- Static type checkers mostly care about the underlying type.
- Frameworks such as FastAPI and Pydantic can also consume the attached metadata.
- That makes `Annotated` a central meeting point between typing and runtime behavior.

## When Aliases Help

<div class="doc-checklist">
  <div class="check-card">
    <h3>Domain meaning appears</h3>
    <p>Names such as `UserId`, `OrderNumber`, or `Slug` make the API intent clearer than plain primitives.</p>
  </div>
  <div class="check-card">
    <h3>Complex unions repeat</h3>
    <p>Long repeated type expressions often read much better once named.</p>
  </div>
  <div class="check-card">
    <h3>Metadata needs reuse</h3>
    <p>`Annotated` aliases can package both type meaning and reusable metadata.</p>
  </div>
  <div class="check-card">
    <h3>Avoid premature aliases</h3>
    <p>Wrapping every simple type in an alias can make code harder to read, not easier.</p>
  </div>
</div>

## Official Sources

- [typing](https://docs.python.org/3/library/typing.html)
- [PEP 695: Type Parameter Syntax](https://peps.python.org/pep-0695/)
