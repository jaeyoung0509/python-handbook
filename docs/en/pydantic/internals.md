# Internals

<p class="lead">This chapter is about the internal shape of Pydantic: what gets prepared at class-definition time, what gets cached, and why some extension points are easy while others push you closer to pydantic-core internals. You do not need to become a library author to benefit from this model.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: when a Pydantic model class is defined, it collects fields and annotations, builds core schema, and prepares a `SchemaValidator` plus `SchemaSerializer`. Rebuilds are only needed when annotation resolution was incomplete, such as with forward references or dynamic model construction.</p>
</div>

## Internal Flow

<MermaidDiagram
  caption="Model classes prepare their field metadata and compiled validation/serialization helpers up front."
  chart="flowchart LR; A[Class body and annotations] --> B[model_fields build]; B --> C[Annotation resolution and config merge]; C --> D[Core schema generation]; D --> E[SchemaValidator]; D --> F[SchemaSerializer]; E --> G[model_validate path]; F --> H[model_dump path];"
/>

## What You Can Inspect Directly

```py
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


print(User.model_fields)
print(type(User.__pydantic_validator__).__name__)
print(type(User.__pydantic_serializer__).__name__)
```

<p class="code-caption">A model class already carries `model_fields`, `__pydantic_validator__`, and `__pydantic_serializer__`. Validation is not reinterpreted from scratch on every call.</p>

## Why Annotation Resolution Matters

- Forward references may need a later rebuild.
- Generic and recursive models depend on annotation resolution order.
- Frameworks that consume annotations and build Pydantic schemas depend on the same runtime behavior.

## When `model_rebuild()` Enters the Picture

- a forward reference was not yet resolvable
- a model was assembled dynamically
- generic parameters or delayed imports left the first schema incomplete

## The Feel of Caching and Reuse

- Each model class owns prepared validator and serializer objects.
- `TypeAdapter` also prepares reusable validation and serialization objects.
- In hot paths, reuse model classes and adapters instead of recreating them repeatedly.

## Framework-Facing Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Annotation reading</h3>
    <p>Frameworks often do not use annotations directly; they feed them into schema generation first.</p>
  </div>
  <div class="check-card">
    <h3>Schema cache</h3>
    <p>Reusing the same model or adapter means reusing prepared validator/serializer machinery.</p>
  </div>
  <div class="check-card">
    <h3>Dynamic model cost</h3>
    <p>Dynamic generation and rebuilds are powerful, but more complex to reason about than static declarations.</p>
  </div>
  <div class="check-card">
    <h3>Custom hooks</h3>
    <p>The deeper you go into custom schema hooks, the more this internal model matters.</p>
  </div>
</div>

## Official Sources

- [Pydantic Architecture](https://docs.pydantic.dev/latest/internals/architecture/)
- [Resolving Annotations](https://docs.pydantic.dev/latest/internals/resolving_annotations/)
