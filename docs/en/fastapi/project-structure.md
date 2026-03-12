# Project Structure

<p class="lead">FastAPI makes it easy to ship the first endpoint. The real challenge is preventing route functions from becoming a dump for validation, transactions, domain rules, and serialization.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: keep routes thin, move business rules into services, treat persistence as its own layer, and use Pydantic models for boundary contracts rather than as your entire application model.</p>
</div>

## Start With the Request Flow

<MermaidDiagram
  caption="Routes handle the HTTP boundary. Services hold business decisions. Persistence and serialization live at explicit edges."
  chart="flowchart LR; A[Client] --> B[FastAPI Router]; B --> C[Service Layer]; C --> D[Repository or Unit of Work]; D --> E[(Database)]; C --> F[Domain Model]; B --> G[Pydantic Request/Response Models];"
/>

## Why It Matters

- When routes own every responsibility, testing becomes harder and imports get tangled.
- Pydantic models and ORM models have different jobs, so treating them as the same type usually creates churn.
- Async endpoints do not automatically imply clean architecture.

## A Practical Layout

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
    session.py
  core/
    config.py
  main.py
```

## Small Example

```py
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_factory
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


@router.post("", response_model=UserRead)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.create_user(payload)
```

<p class="code-caption">The route owns HTTP concerns. The service owns business behavior. The session lifecycle is explicit. That separation survives growth far better than a giant route module.</p>

## sub-optimal -> improved: when the route owns everything

### Bad example: a fat route

```py
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/users")
async def create_user_bad(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    if os.getenv("ALLOW_SIGNUP", "false") != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="signup disabled")

    existing = await session.scalar(
        select(UserModel).where(UserModel.email == payload.email)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="duplicate email")

    record = UserModel(email=payload.email, name=payload.name)
    session.add(record)
    await session.commit()
    return UserRead.model_validate(record)
```

<p class="code-caption">This route mixes configuration lookup, domain validation, query shape, commit policy, and response assembly. As the behavior grows, tests become HTTP-heavy and the business rule becomes harder to reuse or verify in isolation.</p>

### Better example: route as transport, service as use case

```py
from fastapi import APIRouter, Depends, status

router = APIRouter()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    command = CreateUserCommand(email=payload.email, name=payload.name)
    return await service.create_user(command)


class UserService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def create_user(self, command: CreateUserCommand) -> UserRead:
        if not self.settings.allow_signup:
            raise SignupDisabled()

        existing = await self.session.scalar(
            select(UserModel).where(UserModel.email == command.email)
        )
        if existing is not None:
            raise DuplicateEmail(command.email)

        record = UserModel(email=command.email, name=command.name)
        self.session.add(record)
        await self.session.commit()
        return UserRead(id=record.id, email=record.email, name=record.name)
```

<p class="code-caption">The improvement is not "more layers at all costs." The real gain is preserving the HTTP boundary, injecting settings explicitly, and making the commit point line up with the business action. That keeps route-contract tests and service-branching tests separate.</p>

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>FastAPI types stay at the edge</h3>
    <p>Keep `Depends`, `Request`, `Response`, and framework-specific objects near the router layer.</p>
  </div>
  <div class="check-card">
    <h3>Separate schemas from ORM entities</h3>
    <p>Boundary contracts and persistence entities evolve for different reasons.</p>
  </div>
  <div class="check-card">
    <h3>Control startup side effects</h3>
    <p>Prefer explicit lifespan or startup wiring over imports that connect clients or mutate global state.</p>
  </div>
</div>

## Code Review Lens

- Check whether the route knows only HTTP parsing, auth, status codes, and response contracts.
- Check whether the service or use case owns transaction boundaries and business branching.
- Check whether settings, loggers, and external clients are injected explicitly rather than pulled from globals ad hoc.
- Check whether ORM entities, request DTOs, and response DTOs remain separate types.

## Common Anti-Patterns

- a route calling `os.getenv()`, querying the DB, committing, and serializing in one function
- returning ORM entities directly so lazy loading leaks into the API contract
- import-time side effects that connect clients or perform app wiring
- repositories or helpers that open their own sessions and commit autonomously

## Likely Discussion Questions

- If you had to add tracing, timeout policy, or retries here, which layer should change first?
- If signup policy becomes tenant-specific, which boundary would feel the change most?
- What would you separate first if you wanted to test duplicate-email behavior without HTTP?
- How do you keep the public API contract stable when ORM models evolve underneath it?

## Strong Answer Frame

- Start by naming the mixed responsibilities in the current code.
- Explain how that shape increases test cost, change surface, and operational ambiguity.
- Move the smallest set of responsibilities so routes stay thin and business actions own commits.
- Close by connecting the refactor to clearer unit tests, integration tests, and observability boundaries.
