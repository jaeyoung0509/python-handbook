# Type Narrowing

<p class="lead">The quality of real-world typing often depends more on narrowing than on declarations. If you cannot safely narrow broad input types after runtime checks, codebases tend to drift toward casts and `Any`.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: narrowing is how runtime checks become static type information. `isinstance`, `match`, `TypeGuard`, and `TypeIs` let you replace many unsafe casts with explicit, checkable flow.</p>
</div>

## Narrowing Picture

<MermaidDiagram
  caption="A broad input type becomes more precise after a runtime check, producing narrower branches for the type checker."
  chart="flowchart LR; A[broad input type] --> B[runtime check]; B --> C[narrowed true branch]; B --> D[narrowed false branch];"
/>

## `TypeGuard` vs `TypeIs`

```py
from typing import TypeGuard, TypeIs


def is_str_list(values: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(value, str) for value in values)


def is_int(value: int | str) -> TypeIs[int]:
    return isinstance(value, int)
```

<p class="code-caption">`TypeGuard` is good when a complex structure should be treated as a more specific type. `TypeIs` is better for true type predicates that behave more like `isinstance` checks.</p>

## `match` Helps Too

```py
def describe(value: int | str | None) -> str:
    match value:
        case int():
            return "int"
        case str():
            return "str"
        case None:
            return "none"
```

## Truthiness Narrowing Has Limits

- `if value:` collapses empty strings, zero, empty collections, and `None`.
- If your design must distinguish "missing" from "empty," truthiness alone is too blunt.

## Practical Connections

- input validation helpers
- discriminator-based branching
- API payload parsing

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Prefer narrowing over casting</h3>
    <p>If possible, make runtime checks visible to the type checker instead of scattering `cast()` calls.</p>
  </div>
  <div class="check-card">
    <h3>Do not overuse truthiness</h3>
    <p>Explicit comparisons are safer when empty and missing values mean different things.</p>
  </div>
  <div class="check-card">
    <h3>Choose `TypeGuard` vs `TypeIs` carefully</h3>
    <p>`TypeGuard` fits structural refinement; `TypeIs` fits true type predicates.</p>
  </div>
  <div class="check-card">
    <h3>Use discriminators</h3>
    <p>Tagged unions with explicit `kind` or `type` fields make both runtime logic and narrowing much cleaner.</p>
  </div>
</div>

## Official Sources

- [typing.TypeGuard](https://docs.python.org/3/library/typing.html#typing.TypeGuard)
- [typing.TypeIs](https://docs.python.org/3/library/typing.html#typing.TypeIs)
