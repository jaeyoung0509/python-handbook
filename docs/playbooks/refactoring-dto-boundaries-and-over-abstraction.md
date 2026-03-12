# Refactoring DTO Boundaries and Over-Abstraction

<p class="lead">DTO/ORM boundary collapse와 over-abstraction은 흔히 같이 온다. 팀은 "중복을 줄이자"는 의도로 request schema, response schema, ORM entity를 하나로 합치고, 동시에 generic repository나 ABC를 넓게 깔아 두는데, 결과는 경계가 흐려지고 concrete behavior가 더 안 보이게 된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 먼저 타입을 더 만들기보다 boundary를 다시 나누는 것이 중요하다. request DTO, response DTO, ORM entity는 분리하고, abstraction은 substitution 가치가 있는 경계에만 남긴다.</p>
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

## 2) 정확한 냄새는 무엇인가

- `UserSchema`가 request, response, persistence mapping 역할을 모두 한다.
- generic repository가 query shape와 transaction ownership 같은 중요한 concrete detail을 숨긴다.
- abstraction은 많은데 실제 교체 가치가 있는 경계는 거의 없다.

이 구조는 처음엔 "중복이 적다"는 장점처럼 보이지만, 필드 역할이 달라지거나 응답 계약이 바뀌는 순간 한 타입 변경이 모든 레이어에 파급된다.

## 3) 가장 작은 안전한 리팩터링 순서

1. request DTO와 response DTO부터 분리한다.
2. ORM entity는 persistence detail로 다시 고정한다.
3. generic repository를 걷어내고 query shape가 보이는 concrete repository를 복원한다.
4. notifier, UoW처럼 substitution/testing 가치가 있는 경계만 ABC로 남긴다.

포인트는 abstraction을 더 정교하게 만드는 것이 아니라, 먼저 잘못 넓어진 abstraction을 줄이는 것이다.

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

## 5) 무엇이 좋아지나

- `tests`: request validation, business rule, persistence mapping, response contract를 다른 테스트 층으로 나눌 수 있다.
- `operations`: serialization 단계에서 lazy load가 튀거나 ORM shape가 API에 새는 일이 줄어든다.
- `change isolation`: API contract를 바꿔도 persistence schema와 abstraction hierarchy를 동시에 흔들지 않아도 된다.

## Code Review Lens

- request DTO, response DTO, ORM entity의 역할이 실제로 분리돼 있는지 본다.
- abstraction이 substitution/testing value가 있는 곳에만 남아 있는지 본다.
- query shape와 transaction ownership이 generic interface 뒤에 숨지 않는지 본다.
- `from_attributes=True`가 boundary collapse를 정당화하는 용도로 쓰이지 않는지 본다.

## Common Anti-Patterns

- request와 response에 같은 schema를 재사용한다.
- ORM entity를 그대로 response model에 태워 계약을 대신하게 한다.
- "SOLID"라는 이유로 repository/service/DTO를 모두 ABC로 만든다.
- generic repository 하나로 모든 entity와 query shape를 덮으려 한다.

## Likely Discussion Questions

- DTO 분리를 어디서부터 시작하는 것이 가장 안전한가?
- 어떤 abstraction은 남기고 어떤 abstraction은 concrete로 되돌려야 하는가?
- generic repository가 가리는 concrete detail은 실제로 무엇인가?
- response DTO를 명시적으로 두면 migration과 contract evolution에 어떤 이점이 생기는가?

## Strong Answer Frame

- 먼저 하나의 타입이 지금 몇 개의 경계를 동시에 대표하고 있는지 드러낸다.
- 그 다음 request DTO, response DTO, ORM entity를 분리해 변화 축을 나눈다.
- substitution 가치가 없는 abstraction을 concrete로 되돌려 query와 transaction ownership을 다시 보이게 만든다.
- 마지막으로 테스트, migration, contract evolution 비용이 어떻게 줄어드는지 연결한다.

## 같이 읽으면 좋은 문서

- [Refactoring Atlas](/playbooks/refactoring-atlas)
- [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)
- [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)
- [Request/Response Modeling](/fastapi/request-response-modeling)
