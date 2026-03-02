# BaseModel vs TypeAdapter

<p class="lead">In Pydantic v2, you no longer need to solve every validation problem by creating a `BaseModel`. `BaseModel` is strong when you need a named schema contract, but `TypeAdapter` is often the better tool for validating arbitrary typed structures such as collections, unions, and `TypedDict`s.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: if you need a named public contract, start with `BaseModel`. If you simply need to validate or serialize a type structure right now, reach for `TypeAdapter` first.</p>
</div>

## Compare the Roles Directly

| Question | `BaseModel` | `TypeAdapter` |
| --- | --- | --- |
| Named field contract needed? | Strong | Weak |
| Model config and methods needed? | Strong | None |
| One-off validation of an arbitrary type? | Often too much | Strong |
| Validate `TypedDict`, `list[T]`, `dict[K, V]` directly? | May need wrapper model | Direct |
| Generate JSON schema? | Yes | Yes |
| Reuse compiled validation for one typed shape? | Via model class | Direct on the adapter |

## When `BaseModel` Is the Right Tool

```py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime
```

- API request and response DTOs
- settings objects
- named boundary contracts

## When `TypeAdapter` Is Better

```py
from typing import TypedDict

from pydantic import TypeAdapter


class Row(TypedDict):
    id: int
    name: str


row_adapter = TypeAdapter(list[Row])

rows = row_adapter.validate_python(
    [{"id": "1", "name": "kim"}, {"id": 2, "name": "lee"}]
)
print(rows)
print(row_adapter.json_schema())
```

<p class="code-caption">If all you want is validation for `list[TypedDict]`, a wrapper model can be more ceremony than value. `TypeAdapter` keeps the code closer to the real typed shape.</p>

## Good Real-World Uses for `TypeAdapter`

- queue or Kafka payload validation
- validating shaped projections from ORM queries
- internal helper functions that only need typed data validation
- reusable constrained primitive or collection types

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Is this a public named contract?</h3>
    <p>If documentation and explicit fields matter, `BaseModel` is usually the natural fit.</p>
  </div>
  <div class="check-card">
    <h3>Is this mostly a validation utility?</h3>
    <p>If the core need is validating an arbitrary type structure, `TypeAdapter` is usually cleaner.</p>
  </div>
  <div class="check-card">
    <h3>Is the type deeply nested?</h3>
    <p>Complex generic shapes are often clearer as a direct adapter target than as a stack of wrapper models.</p>
  </div>
  <div class="check-card">
    <h3>Is this a FastAPI boundary?</h3>
    <p>FastAPI request and response schemas usually align better with `BaseModel`, while internal helpers can use `TypeAdapter` freely.</p>
  </div>
</div>

## Official Sources

- [Type Adapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
- [Models](https://docs.pydantic.dev/latest/concepts/models/)
