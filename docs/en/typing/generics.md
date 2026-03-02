# Generics

<p class="lead">Generics let you build reusable APIs without throwing away type information. Their real value is not type theory for its own sake, but preserving the relationship between input types and output types.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: generics keep reusable code from collapsing into `Any`. Python 3.12+ type-parameter syntax makes generic declarations much easier to read directly where they matter.</p>
</div>

## When Generics Pay Off

<MermaidDiagram
  caption="Generics preserve type information across a reusable API boundary."
  chart="flowchart LR; A[input type T] --> B[generic function or class]; B --> C[output still typed as T];"
/>

## Type Parameter Syntax Example

```py
class Box[T]:
    def __init__(self, value: T) -> None:
        self.value = value

    def unwrap(self) -> T:
        return self.value


def first[T](items: list[T]) -> T:
    return items[0]


type Row[T] = dict[str, T]


print(Box("python").unwrap())
print(first([1, 2, 3]))
print(Row[int])
```

## Why `TypeVar` Still Matters

- A lot of existing code and docs still use the older `TypeVar` style.
- Bounds, constraints, and variance are still usually explained in `TypeVar` terms.
- The new syntax improves readability, but it does not erase the underlying concepts.

## How Much Variance You Need

- Most app developers mainly need a solid grasp of invariance.
- You should know that `list[Derived]` is not a subtype of `list[Base]`.
- Covariance and contravariance matter more for library authors and protocol-heavy APIs.

## Practical Connections

- repository abstractions
- typed containers and helpers
- generic Pydantic models

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Do you need type preservation?</h3>
    <p>Generics are most useful when input and output types are meaningfully linked.</p>
  </div>
  <div class="check-card">
    <h3>Can you avoid `Any`?</h3>
    <p>Reusable APIs should preserve type information whenever possible.</p>
  </div>
  <div class="check-card">
    <h3>Are you overusing variance?</h3>
    <p>Complex variance annotations can hurt readability in ordinary application code.</p>
  </div>
  <div class="check-card">
    <h3>Is the declaration readable?</h3>
    <p>The new syntax helps because generic intent is visible right at the definition site.</p>
  </div>
</div>

## Official Sources

- [typing generics](https://docs.python.org/3/library/typing.html)
- [PEP 695: Type Parameter Syntax](https://peps.python.org/pep-0695/)
