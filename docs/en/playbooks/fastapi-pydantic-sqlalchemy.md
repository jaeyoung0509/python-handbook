# FastAPI + Pydantic + SQLAlchemy

<p class="lead">This page shows how to combine FastAPI, Pydantic, and SQLAlchemy in a way that stays readable under real service growth. The core move is to keep request DTOs, service/use-case logic, sessions and transactions, ORM records, and response DTOs as explicit boundaries.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: let routes own HTTP concerns, let services own business actions, let repositories own persistence details, and keep commits at the use-case boundary. Finish the API with DTOs, not raw ORM entities.</p>
</div>

## End-to-End Flow

<MermaidDiagram
  caption="The API boundary should use DTOs, while the inside uses services, repositories, and one shared session per use case."
  chart="flowchart LR; A[HTTP Request] --> B[Request DTO]; B --> C[Service or Use Case]; C --> D[Repository]; D --> E[SQLAlchemy Session]; E --> F[(Database)]; C --> G[Response DTO]; G --> H[HTTP Response];"
/>

## Recommended Folder Layout

```text
app/
  api/
    routes/
      users.py
  schemas/
    user.py
  services/
    user_service.py
  repositories/
    user_repository.py
  db/
    models.py
    session.py
  domain/
    errors.py
  main.py
```

## Boundary Types in Code

```py
from datetime import datetime
from uuid import UUID

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
```

```py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
```

<p class="code-caption">`CreateUserRequest` and `UserResponse` are API contracts. `UserRecord` is a persistence implementation detail. Keeping them separate makes both layers easier to change.</p>

## Let the Service Own the Transaction

```py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserRecord).where(UserRecord.email == email)
        return await self.session.scalar(stmt)

    def add(self, record: UserRecord) -> None:
        self.session.add(record)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def create_user(self, payload: CreateUserRequest) -> UserResponse:
        async with self.session.begin():
            if await self.users.get_by_email(payload.email) is not None:
                raise DuplicateEmail(payload.email)

            record = UserRecord(
                email=payload.email,
                name=payload.name,
            )
            self.users.add(record)
            await self.session.flush()

            return UserResponse.model_validate(record)
```

## Keep the Route Thin

```py
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(session)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.create_user(payload)
```

## Design Reads and Writes Differently

### Write path

- Transaction boundaries matter most.
- Use `flush()` when you need generated values or early constraint feedback.
- Build a response DTO without relying on lazy loads.

### Read path

- A commit is often unnecessary.
- Choose loading strategies explicitly.
- Shape the result for the API instead of leaking ORM graphs.

## A Near-Ideal API Design Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>ORM stays internal</h3>
    <p>Public contracts are DTOs, not ORM entities. Persistence changes should not force API changes.</p>
  </div>
  <div class="check-card">
    <h3>One use case, one transaction</h3>
    <p>Let each business action own one atomic boundary.</p>
  </div>
  <div class="check-card">
    <h3>Map domain errors to HTTP</h3>
    <p>Define domain errors like `DuplicateEmail` first, then translate them to status codes in routes or exception handlers.</p>
  </div>
  <div class="check-card">
    <h3>Stop N+1 during serialization</h3>
    <p>Load what the response needs before building the DTO. Do not let serializers trigger database access.</p>
  </div>
</div>

The more interface-driven use-case plus class-based UoW pattern is covered separately in [Use Case + UoW + Interface](/en/playbooks/usecase-uow-and-interfaces).

## Avoid These Patterns

- Routes that call `session.add()`, `session.commit()`, and `UserResponse.model_validate()` directly
- Repository methods that commit on their own
- Reusing one schema for request and response when the field roles differ
- Returning ORM objects and hoping the response model will sort everything out

## Official Sources

- [FastAPI SQL Databases Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy AsyncIO Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
