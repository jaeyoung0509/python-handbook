# Core Schema

<p class="lead">The heart of Pydantic v2 is that `BaseModel` does not directly perform validation. Instead, Pydantic turns annotations and constraints into an intermediate representation called core schema, and `pydantic-core` executes that schema. Once you see that structure, Pydantic's performance model and extension model become much clearer.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: core schema is the compiled graph of your Python type hints, constraints, and hooks. `BaseModel`, `Annotated`, field constraints, validators, and `TypeAdapter` are all ways of producing or consuming that schema.</p>
</div>

## Start With the Flow

<MermaidDiagram
  caption="Pydantic does not validate annotations directly. It first builds core schema and then lets pydantic-core execute it."
  chart="flowchart LR; A[Python annotations and constraints] --> B[Pydantic schema builder]; B --> C[Core schema graph]; C --> D[SchemaValidator in pydantic-core]; C --> E[SchemaSerializer in pydantic-core]; D --> F[Python objects or ValidationError]; E --> G[dict, JSON-ready output, JSON schema];"
/>

## Why It Matters

- It explains why `TypeAdapter` can validate arbitrary types without a model class.
- It explains how validators, field constraints, and `Annotated` metadata combine.
- It gives you the right mental model for custom types and framework integrations.

## A Minimal Code Example

```py
from typing import Annotated

from pydantic import AfterValidator, BaseModel, TypeAdapter


def positive(value: int) -> int:
    if value <= 0:
        raise ValueError("positive only")
    return value


PositiveInt = Annotated[int, AfterValidator(positive)]


class LineItem(BaseModel):
    qty: PositiveInt


adapter = TypeAdapter(list[PositiveInt])

print(LineItem.model_validate({"qty": "3"}))
print(adapter.validate_python(["1", 2, 3]))
print("adapter core schema type:", adapter.core_schema["type"])
```

<p class="code-caption">`LineItem` and `TypeAdapter(list[PositiveInt])` look like different APIs, but both are built on top of core schema and the same pydantic-core validator machinery.</p>

## What Usually Ends Up in Core Schema

- primitive and container type information
- structure for models, unions, and nested types
- constraints such as length, bounds, regex, and strictness
- hooks from validators and serializers
- metadata carried by `Annotated`

## Why `Annotated` Matters

In Pydantic v2, many useful runtime validation hooks are expressed through `Annotated`, so typing metadata and runtime validation metadata meet in the same declaration site.

```py
from typing import Annotated
from pydantic import Field, TypeAdapter

UserId = Annotated[int, Field(gt=0, description="database primary key")]

adapter = TypeAdapter(UserId)
print(adapter.validate_python("10"))
```

## When You Need Core-Schema Intuition

<div class="doc-checklist">
  <div class="check-card">
    <h3>Custom reusable types</h3>
    <p>You want validation rules to live at the type level rather than inside one model field.</p>
  </div>
  <div class="check-card">
    <h3>TypeAdapter reuse</h3>
    <p>You want fast validation for arbitrary typed structures without wrapping them in model classes.</p>
  </div>
  <div class="check-card">
    <h3>Framework integration</h3>
    <p>You are reading annotations and turning them into schemas or validators.</p>
  </div>
  <div class="check-card">
    <h3>Performance reasoning</h3>
    <p>You want to understand that Pydantic is not running ad hoc Python checks from scratch for every input.</p>
  </div>
</div>

## Official Sources

- [Pydantic Architecture](https://docs.pydantic.dev/latest/internals/architecture/)
- [Type Adapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
