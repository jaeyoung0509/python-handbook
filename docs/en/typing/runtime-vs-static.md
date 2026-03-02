# Runtime vs Static

<p class="lead">Python typing lives in two different worlds at once: the static world of type checkers and the runtime world of frameworks that inspect annotations directly. If you blur those worlds together, `Annotated`, deferred annotations, FastAPI, and Pydantic quickly become confusing.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: type checkers read annotations for static meaning, while runtime tools read annotations as objects or expressions they can inspect. `Annotated` and `annotationlib` are especially important at this boundary.</p>
</div>

## Separate the Two Views

<MermaidDiagram
  caption="The same annotation serves different consumers: static analyzers and runtime frameworks do not use it for the same purpose."
  chart="flowchart LR; A[Python annotation] --> B[static type checker]; A --> C[runtime annotation reader]; B --> D[type compatibility and narrowing]; C --> E[framework metadata, dependency wiring, validation schema];"
/>

## A Small Example

```py
from typing import Annotated

import annotationlib


def endpoint(
    user_id: Annotated[int, "path parameter"],
) -> Annotated[str, "response body"]:
    return str(user_id)


print(
    annotationlib.get_annotations(
        endpoint,
        format=annotationlib.Format.STRING,
    )
)
print(endpoint.__annotations__)
```

<p class="code-caption">A type checker mainly cares about `int` and `str`. Runtime tools can also inspect metadata inside `Annotated` and can work with deferred annotation forms through `annotationlib`.</p>

## What FastAPI and Pydantic Consume

- FastAPI reads parameter annotations and `Annotated` metadata to build request parsing and OpenAPI descriptions.
- Pydantic reads annotations to build core schema for validation and serialization.
- So annotations are no longer just static comments for tooling.

## Key Questions

- Why do type checkers know things the runtime does not?
- Which parts of an annotation are types and which parts are metadata?

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Separate static and runtime meaning</h3>
    <p>Type checkers infer without executing code; frameworks read annotation objects at runtime.</p>
  </div>
  <div class="check-card">
    <h3>Use `Annotated` intentionally</h3>
    <p>It is a strong tool for carrying both type meaning and runtime metadata, but the two roles should stay conceptually separate.</p>
  </div>
  <div class="check-card">
    <h3>Understand annotation reading cost</h3>
    <p>Deferred annotations and `annotationlib` exist partly to reduce forward-reference and import-cycle pain.</p>
  </div>
  <div class="check-card">
    <h3>Know how frameworks consume annotations</h3>
    <p>FastAPI, Pydantic, and ORMs can treat annotations as runtime metadata, not just type hints.</p>
  </div>
</div>

## Official Sources

- [annotationlib](https://docs.python.org/3/library/annotationlib.html)
- [typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated)
