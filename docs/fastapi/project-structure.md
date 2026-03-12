# Project Structure

<p class="lead">FastAPI는 몇 파일로 빨리 시작하기 쉽다. 문제는 그 편리함 때문에 route 함수가 validation, transaction, domain logic, serialization을 다 끌어안기 쉽다는 점이다. 구조를 빨리 잘 잡는 것이 성능보다 먼저 중요하다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: FastAPI route는 HTTP 경계만 맡고, 비즈니스 규칙은 service, 영속성은 repository 또는 unit-of-work, 입출력 계약은 Pydantic schema로 분리하는 편이 가장 오래 버틴다.</p>
</div>

## 먼저 구조 그림부터

<MermaidDiagram
  caption="요청은 router에서 받아 service로 전달하고, DB 접근과 직렬화 책임은 바깥 레이어로 분리한다."
  chart="flowchart LR; A[Client] --> B[FastAPI Router]; B --> C[Service Layer]; C --> D[Repository or Unit of Work]; D --> E[(Database)]; C --> F[Domain Model]; B --> G[Pydantic Request/Response Models];"
/>

## 왜 중요한가

- route 함수에 모든 책임이 몰리면 테스트가 어려워지고 import 의존성이 꼬인다.
- Pydantic model과 ORM model을 그대로 섞으면 경계가 흐려져서 변경 비용이 커진다.
- async endpoint라고 해서 내부가 자동으로 "좋은 구조"가 되지는 않는다.

## 추천 폴더 구조

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

## 작게 보이는 좋은 예

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

<p class="code-caption">route는 HTTP 입력을 받아 service에 넘기고, response model만 명확히 보장한다. transaction, domain rule, ORM 세부 구현은 안쪽 레이어로 미룬다.</p>

## sub-optimal -> improved: route가 모든 책임을 끌어안는 경우

### 나쁜 예: fat route

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

<p class="code-caption">이 route는 설정 조회, 도메인 검증, query shape, commit 정책, 응답 조립을 한 함수에 섞는다. 이런 구조는 로직이 늘수록 HTTP 테스트만 두꺼워지고, business rule을 재사용하거나 단위 테스트하기가 어려워진다.</p>

### 더 나은 예: route는 transport, service는 use case

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

<p class="code-caption">개선 포인트는 계층 수를 늘리는 데 있지 않다. route가 HTTP 경계를 지키고, settings는 주입받고, commit 위치가 business action과 같이 읽히도록 만드는 데 있다. 이렇게 해야 테스트도 route contract와 service branching으로 분리된다.</p>

## 실전에서 자주 헷갈리는 기준

<div class="doc-checklist">
  <div class="check-card">
    <h3>FastAPI 의존성 범위</h3>
    <p>`Depends`, `Request`, `Response` 같은 FastAPI 전용 타입은 최대한 router 바깥으로 새지 않게 두는 편이 좋다.</p>
  </div>
  <div class="check-card">
    <h3>Schema와 ORM 분리</h3>
    <p>Pydantic request/response model과 SQLAlchemy entity는 역할이 다르다. 같은 타입으로 통합하려고 하면 경계가 무너진다.</p>
  </div>
  <div class="check-card">
    <h3>Import side effect</h3>
    <p>startup에서 연결해야 할 것과 import만으로 실행되는 것을 분리해야 테스트와 앱 초기화가 안정적이다.</p>
  </div>
</div>

## Code Review Lens

- route가 HTTP parsing, auth, status code, response contract만 알고 있는지 본다.
- service/use case가 transaction 경계와 business branching을 소유하는지 본다.
- settings, logger, external client가 ad-hoc global lookup 대신 명시적으로 주입되는지 본다.
- ORM entity, request DTO, response DTO가 한 타입으로 뭉개지지 않았는지 본다.

## Common Anti-Patterns

- route 함수가 `os.getenv()`, query, commit, serialization을 모두 수행한다.
- response로 ORM entity를 직접 반환해 lazy load와 API contract가 뒤섞인다.
- import 시점 side effect로 client 연결이나 app wiring이 실행된다.
- repository/helper가 자체적으로 session을 만들고 commit까지 해버린다.

## Likely Discussion Questions

- 이 route에 tracing, timeout, retry policy를 넣어야 하면 어느 레이어를 바꾸는가?
- signup 정책이 tenant별로 달라지면 지금 구조에서 어떤 경계가 먼저 흔들리는가?
- duplicate email 검증을 HTTP 없이 빠르게 테스트하려면 무엇을 분리해야 하는가?
- ORM model이 바뀌어도 외부 API contract를 안정적으로 유지하려면 어디를 고정해야 하는가?

## Strong Answer Frame

- 먼저 현재 코드에서 책임이 섞인 지점을 boundary 기준으로 짚는다.
- 그 구조가 테스트 비용, 변경 반경, 운영 가시성에 어떤 문제를 만드는지 설명한다.
- 가장 작은 리팩터링으로 route를 얇게 하고 commit과 business rule을 안쪽으로 이동시킨다.
- 마지막으로 unit test, integration test, observability 포인트가 어떻게 선명해지는지 연결한다.
