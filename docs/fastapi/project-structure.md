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
