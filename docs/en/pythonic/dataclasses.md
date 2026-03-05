# Dataclasses

<p class="lead">`dataclass` is Python's most natural tool for building lightweight structured objects. It is more than a convenience decorator for `__init__`; it is a clean way to model value objects, internal command payloads, settings, and pattern-matching nodes without hand-writing repetitive boilerplate.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a dataclass is not a validation engine or an ORM replacement. It is a value-oriented class generator that removes boilerplate around initialization, equality, and representation. In practice, `frozen=True`, `slots=True`, `kw_only=True`, `default_factory`, and `__post_init__()` are the combinations worth knowing deeply.</p>
</div>

## The Mental Model

<MermaidDiagram
  caption="A dataclass does not replace the class model. It keeps the class and generates methods that make value-oriented usage much lighter."
  chart="flowchart LR; A[&quot;Annotated class body&quot;] --> B[&quot;@dataclass decorator&quot;]; B --> C[&quot;Generated __init__, __repr__, __eq__&quot;]; B --> D[&quot;Optional frozen, slots, kw_only, match_args&quot;]; C --> E[&quot;Value object or internal payload&quot;];"
/>

## When Dataclasses Fit Extremely Well

- value objects
- internal commands and queries
- settings objects
- pattern-matching nodes
- fixture data bundles in tests

## When They Are a Poor Fit

- external input boundaries that need strong runtime validation
- ORM entities with richer lifecycle and lazy loading
- framework objects that rely on dynamic attributes

## A Safe High-Value Combination

```py
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True, kw_only=True)
class RetryPolicy:
    max_attempts: int
    base_delay_ms: int = 100
    retry_on: tuple[str, ...] = field(default_factory=lambda: ("timeout", "busy"))
```

<p class="code-caption">`frozen=True` is excellent for immutable value-object semantics, `slots=True` makes the instance shape tighter, and `kw_only=True` reduces positional-call mistakes in settings and command payloads.</p>

## Why `default_factory` Matters

```py
from dataclasses import dataclass, field


@dataclass
class Batch:
    job_id: str
    items: list[str] = field(default_factory=list)
```

- Mutable defaults should not be written as `[]`, `{}`, or `set()` directly.
- The official dataclasses docs explicitly recommend `default_factory` for this reason.

## `__post_init__()` Is the Normalization Hook

```py
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if "@" not in normalized:
            raise ValueError("invalid email address")
        object.__setattr__(self, "value", normalized)
```

`__post_init__()` is great for normalization and cross-field invariants. But once this grows into a full input-validation framework, a separate validation boundary such as Pydantic often becomes a better fit.

## Dataclasses and Pattern Matching Work Well Together

- Dataclasses can generate `__match_args__`.
- That makes them pleasant for AST-like nodes or internal command objects used with `match/case`.
- Python 3.10's `match_args` and `kw_only` settings connect directly to that style.

## Practical Guidance

| Situation | Good default |
| --- | --- |
| internal value object | `frozen=True`, and often `slots=True` |
| settings or command payload | use `kw_only=True` aggressively |
| list/dict/set field | use `default_factory` |
| API boundary | keep validation separate |
| ORM entity | do not force dataclass and ORM concerns into one model |

## Common Mistakes

- using mutable defaults directly
- treating dataclasses like request validators
- relying on mutable objects while thinking in value-object terms
- collapsing ORM models, dataclass DTOs, and Pydantic schemas together

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Is this a value object?</h3>
    <p>Dataclasses work best when data shape and equality matter more than rich behavior.</p>
  </div>
  <div class="check-card">
    <h3>Are mutable defaults avoided?</h3>
    <p>Use `default_factory` for list, dict, and set fields by default.</p>
  </div>
  <div class="check-card">
    <h3>Is validation separated?</h3>
    <p>External boundaries usually need runtime validation beyond what a dataclass alone should own.</p>
  </div>
  <div class="check-card">
    <h3>Would keyword-only be safer?</h3>
    <p>For settings-like or longer payload types, `kw_only=True` often improves call-site clarity.</p>
  </div>
</div>

## Official References

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [PEP 557](https://peps.python.org/pep-0557/)
