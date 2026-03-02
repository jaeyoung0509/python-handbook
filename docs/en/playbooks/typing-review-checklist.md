# Typing Review Checklist

<p class="lead">A team can "use typing" and still have poor type quality. Hidden `Any`, meaningless aliases, confused validation boundaries, and over-abstracted protocols can create the illusion of safety without much real value. This chapter focuses on the review questions that matter.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: good typing review is boundary review. The important questions are whether public signatures explain intent, whether `Any` is contained, whether protocols and concrete types are chosen intentionally, and whether runtime validation concerns are being confused with static typing.</p>
</div>

## A Typing Review Flow

<MermaidDiagram
  caption="Start with boundary clarity, not annotation count."
  chart="flowchart LR; A[Public function or class] --> B{Is the boundary explicit?}; B -->|No| C[Fix signature and DTOs]; B -->|Yes| D{Does Any leak?}; D -->|Yes| E[Constrain boundary types]; D -->|No| F{Protocol or concrete type chosen well?}; F -->|No| G[Refine abstraction]; F -->|Yes| H[Check validation and runtime assumptions];"
/>

## 1. Are Public Signatures Descriptive?

- Do parameter and return types describe the API from the caller's perspective?
- Could `dict[str, Any]` become a `TypedDict`, DTO, or protocol?
- Is the public API coupled too tightly to internal implementation types?

## 2. Does `Any` Leak Past the Boundary?

```py
from typing import Any


def parse_payload(raw: dict[str, Any]) -> CreateUserCommand:
    ...
```

Some `Any` at raw-input boundaries is unavoidable. The important question is whether it gets constrained immediately or continues leaking into services, repositories, and domain logic.

## 3. Do Aliases Add Meaning?

### Good aliases

- add domain meaning
- reduce repeated structural noise
- improve API readability and reuse

### Weak aliases

- only shorten generic containers
- wrap trivial one-off types and make code harder to read

## 4. Are Protocols and Concrete Types Chosen Intentionally?

- Protocols are useful at extension points.
- Concrete types are often clearer inside stable internal layers.
- If everything becomes a protocol, the abstraction may be decorative rather than useful.

## 5. Are Validation and Typing Responsibilities Mixed?

- typing describes a contract between callers and implementations
- validation handles untrusted input at runtime
- an annotation like `str` does not automatically make incoming JSON safe
- good service boundaries validate first, then pass narrower types inward

## Review Smells to Notice Quickly

| Smell | Why it matters | Typical fix |
| --- | --- | --- |
| `Any` everywhere in services | static analysis becomes weak | constrain input with DTOs or `TypedDict` |
| frequent `cast()` calls | the type model and data flow disagree | add predicates, `TypeGuard`, or better validation boundaries |
| too many protocols | abstraction leads the design instead of serving it | keep protocols only where substitution matters |
| request, response, and ORM types collapsed | responsibilities become hard to evolve | split DTOs and entities |
| alias explosion | type reading slows down | keep only aliases with real semantic value |

## Review Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Boundary first</h3>
    <p>Can you understand the external contract of the function or class from its types alone?</p>
  </div>
  <div class="check-card">
    <h3>`Any` containment</h3>
    <p>Even if `Any` exists near raw input, is it constrained before it reaches deeper layers?</p>
  </div>
  <div class="check-card">
    <h3>Abstraction discipline</h3>
    <p>Do protocols, generics, and aliases create real flexibility, or are they decorative complexity?</p>
  </div>
  <div class="check-card">
    <h3>Runtime reality</h3>
    <p>Does the design still account for runtime validation and serialization instead of trusting annotations alone?</p>
  </div>
</div>

## Good Supporting Examples

- `examples/py310_typing_and_zip_strict.py`
- `examples/py312_type_params.py`
- `examples/pydantic_validation_pipeline.py`

## Official References

- [Python typing](https://docs.python.org/3/library/typing.html)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [Pydantic Type Adapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
