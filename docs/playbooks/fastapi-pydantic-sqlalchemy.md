# FastAPI + Pydantic + SQLAlchemy

<p class="lead">이 페이지는 세 라이브러리를 "각자 잘 쓰는 법"이 아니라, 실제 서비스에서 서로 덜 꼬이게 결합하는 구조로 정리한다. 핵심은 request DTO, service/use case, session/transaction, ORM entity, response DTO의 경계를 분명하게 두는 것이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: FastAPI route는 HTTP와 schema만 담당하고, business rule은 service가, persistence는 SQLAlchemy repository가 맡는다. commit은 use case 경계에서 한 번만 일어나고, 응답은 ORM이 아니라 DTO로 끝내는 편이 가장 안정적이다.</p>
</div>

## 전체 흐름

<MermaidDiagram
  caption="요청 DTO와 응답 DTO를 바깥 경계로 두고, 그 사이에서 service와 repository가 같은 session을 공유하는 형태가 가장 관리하기 쉽다."
  chart="flowchart LR; A[HTTP Request] --> B[Request DTO]; B --> C[Service or Use Case]; C --> D[Repository]; D --> E[SQLAlchemy Session]; E --> F[(Database)]; C --> G[Response DTO]; G --> H[HTTP Response];"
/>

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
    models.py
    session.py
  domain/
    errors.py
  main.py
```

## 경계를 코드로 보면 이렇다

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

<p class="code-caption">`CreateUserRequest`와 `UserResponse`는 API 계약이고, `UserRecord`는 persistence 구현이다. 둘을 하나의 타입으로 합치지 않는 것이 장기적으로 훨씬 덜 아프다.</p>

## service가 트랜잭션을 소유하는 예

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

## FastAPI route는 얇게 유지한다

```py
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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

## 읽기 경로와 쓰기 경로를 다르게 본다

### write path

- `session.begin()` 또는 `session.commit()` 경계가 중요하다.
- `flush()`로 PK와 제약 오류를 조기에 확인한다.
- 응답 DTO는 lazy load 없이 바로 만들 수 있어야 한다.

### read path

- commit이 필요 없는 경우가 많다.
- 관계 로딩은 `selectinload()` 같은 전략으로 명시한다.
- API shape에 맞춰 projection 또는 DTO 조립을 명시적으로 한다.

## "완벽에 가까운" API 설계를 위한 기준

<div class="doc-checklist">
  <div class="check-card">
    <h3>ORM은 내부 구현</h3>
    <p>공개 API는 ORM entity가 아니라 DTO를 계약으로 삼는다. persistence 변경과 API 변경을 분리할 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>한 use case, 한 트랜잭션</h3>
    <p>회원 생성, 주문 생성 같은 business action이 하나의 atomic boundary를 갖게 한다.</p>
  </div>
  <div class="check-card">
    <h3>도메인 에러를 HTTP로 매핑</h3>
    <p>`DuplicateEmail`, `OrderNotFound` 같은 에러를 먼저 정의하고, route나 exception handler에서 HTTP status로 바꾼다.</p>
  </div>
  <div class="check-card">
    <h3>N+1을 직렬화 단계에서 막기</h3>
    <p>응답 DTO를 만들 때 필요한 관계는 쿼리 단계에서 로드해 둔다. serializer가 DB를 건드리게 두지 않는다.</p>
  </div>
</div>

인터페이스 기반 use case와 class-based UoW 조합은 [Use Case + UoW + Interface](/playbooks/usecase-uow-and-interfaces)에서 별도로 더 깊게 다룬다.

## 하지 않는 편이 좋은 것

- route 함수 안에서 바로 `session.add()`, `session.commit()`, `UserResponse.model_validate(record)`를 다 해버리는 것
- repository 메서드 내부에서 commit하는 것
- request schema와 response schema를 하나로 재활용하는 것
- ORM object를 그대로 반환해서 response_model이 알아서 해결해주길 기대하는 것

## 공식 자료

- [FastAPI SQL Databases Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy AsyncIO Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
