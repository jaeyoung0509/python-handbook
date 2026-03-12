# Refactoring DTO Boundaries and Over-Abstraction

<p class="lead">DTO/ORM boundary collapse and over-abstraction often appear together. Teams try to reduce duplication by merging request schemas, response schemas, and ORM entities, while also layering generic repositories or ABCs everywhere. The result is fewer visible boundaries and less visible concrete behavior.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: the first repair is not "more sophisticated abstractions." It is splitting the boundaries again. Keep request DTOs, response DTOs, and ORM entities separate, and keep abstractions only where substitution genuinely matters.</p>
</div>

## 1) sub-optimal snippet

```py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound=BaseModel)


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    email: str
    name: str
    created_at: datetime | None = None


class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    def save(self, item: T) -> T: ...


class SqlAlchemyUserRepository(AbstractRepository[UserSchema]):
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, item: UserSchema) -> UserSchema:
        record = UserRecord(**item.model_dump(exclude_none=True))
        self.session.add(record)
        self.session.commit()
        return UserSchema.model_validate(record)


@router.post("/users", response_model=UserSchema)
def create_user(
    payload: UserSchema,
    repository: AbstractRepository[UserSchema] = Depends(get_user_repository),
) -> UserSchema:
    return repository.save(payload)
```

## 2) What is the exact smell?

- `UserSchema` is doing request, response, and persistence-mapping work at once.
- The generic repository hides query shape and transaction ownership that are actually important details.
- There is a lot of abstraction, but very little real substitution value.

It feels DRY at first, but once field roles diverge or response contracts evolve, one type change now ripples across every layer.

## 3) The smallest safe refactor sequence

1. Split request DTOs and response DTOs first.
2. Re-anchor ORM entities as persistence detail.
3. Remove the generic repository and restore a concrete repository with visible query shape.
4. Keep ABCs only for boundaries with real substitution or test value.

The point is not to refine the abstraction stack. The point is to reduce the abstraction that is hiding the important behavior.

## 4) improved end state

```py
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    created_at: datetime


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: UserRecord) -> None:
        self.session.add(record)


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def create_user(self, command: CreateUserCommand) -> UserResponse:
        with self.session.begin():
            record = UserRecord(email=command.email, name=command.name)
            self.users.add(record)
            self.session.flush()
            return UserResponse.model_validate(record)
```

## 5) What gets better

- `tests`: request validation, business rules, persistence mapping, and response contracts can be tested at different layers.
- `operations`: serializers stop leaking lazy loads and ORM shape into the API boundary.
- `change isolation`: API contract changes stop forcing persistence and abstraction-hierarchy changes at the same time.

## Code Review Lens

- Check whether request DTOs, response DTOs, and ORM entities play distinct roles.
- Check whether abstractions remain only where substitution or testing value is real.
- Check whether query shape and transaction ownership are hidden behind generic interfaces.
- Check whether `from_attributes=True` is being used to excuse boundary collapse.

## Common Anti-Patterns

- reusing one schema for both request and response
- returning ORM entities directly and treating the response model as the boundary
- turning repositories, services, and DTOs all into ABCs because "SOLID"
- covering every entity and query shape with one generic repository

## Likely Discussion Questions

- What is the safest first step when DTO boundaries have collapsed?
- Which abstractions should survive, and which should be turned back into concrete code?
- What concrete detail does a generic repository often hide?
- How do explicit response DTOs help with migrations and contract evolution?

## Strong Answer Frame

- Start by showing how many boundaries one type is currently pretending to represent.
- Then split request DTOs, response DTOs, and ORM entities so each change axis becomes explicit.
- Remove low-value abstractions until query shape and transaction ownership are visible again.
- Close by connecting the refactor to lower testing cost, safer migrations, and cleaner API contracts.

## Good companion chapters

- [Refactoring Atlas](/en/playbooks/refactoring-atlas)
- [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
- [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)
- [Request/Response Modeling](/en/fastapi/request-response-modeling)
