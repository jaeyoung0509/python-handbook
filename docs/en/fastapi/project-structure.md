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
