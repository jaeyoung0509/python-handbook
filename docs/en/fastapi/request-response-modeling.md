# Request / Response Modeling

<p class="lead">In FastAPI, schemas are not just validation helpers. They are the public contract of your API. Once request DTOs, internal commands, ORM entities, and response DTOs collapse into one type, versioning, security, lazy loading, and serialization costs all get tangled together.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: treat `request model != response model != ORM model` as the default. Explicit inputs and explicit outputs produce APIs that evolve much more safely.</p>
</div>

## The Boundary Model

<MermaidDiagram
  caption="Separating request DTOs, service inputs, ORM records, and response DTOs keeps API evolution and persistence evolution from becoming the same problem."
  chart="flowchart LR; A[Request JSON] --> B[Pydantic Request DTO]; B --> C[Service Command]; C --> D[ORM Model]; D --> E[Response DTO]; E --> F[Response JSON];"
/>

## Baseline Pattern

```py
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    created_at: datetime


PageSize = Annotated[int, Query(ge=1, le=100)]
```

## Why Request and Response Models Should Differ

- Create requests may contain write-only fields like passwords or invitation codes.
- Responses need server-owned fields such as IDs, timestamps, and status.
- ORM records may have persistence-only fields like `password_hash`, soft-delete columns, or version counters.

## `response_model` Is Both Filter and Contract

```py
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
)
async def create_user(payload: CreateUserRequest) -> UserResponse:
    ...
```

<p class="code-caption">In FastAPI, `response_model` is not just for documentation. It shapes serialization and narrows the public contract. That is why returning an explicit response DTO is safer than leaking raw ORM entities.</p>

## Design Rules for Durable APIs

<div class="doc-checklist">
  <div class="check-card">
    <h3>Split input and output</h3>
    <p>Do not reuse one schema for create, update, and read if the field meaning differs.</p>
  </div>
  <div class="check-card">
    <h3>Keep server-owned fields explicit</h3>
    <p>IDs, timestamps, and version counters usually belong in responses, not requests.</p>
  </div>
  <div class="check-card">
    <h3>Fix pagination and error shapes early</h3>
    <p>Stable list and error envelopes save a lot of migration pain later.</p>
  </div>
  <div class="check-card">
    <h3>Stop ORM leakage</h3>
    <p>Build DTOs explicitly so serialization never depends on hidden lazy loads.</p>
  </div>
</div>

## Practical Rules

- Use dedicated `CreateXRequest`, `UpdateXRequest`, and `XResponse` models.
- Keep response DTOs stable even if persistence columns change.
- Use `Annotated` plus `Query`, `Path`, and `Header` to make constraints visible in the function signature.
- Keep list responses consistent with `items + page info`.

## Official Sources

- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [FastAPI Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)
