# Use Case + UoW + ABC

<p class="lead">이 페이지는 SOLID를 Python 서비스 코드로 번역할 때, `Protocol`보다 `abc.ABC`를 선호하는 팀을 위한 기준 문서다. 핵심은 "모든 계층을 추상화"하는 것이 아니라, use case가 진짜로 의존하는 경계만 명시적 추상 클래스로 고정하고 SQLAlchemy 구현은 바깥에 두는 것이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: use case는 `AbstractUnitOfWork`, `AbstractNotifier` 같은 작은 ABC에만 의존하고, SQLAlchemy session/repository wiring은 concrete UoW가 맡는다. 명시적 추상 클래스는 런타임에서도 계약을 드러내기 쉬워서 팀 코드 리뷰와 fake 구현 작성에 유리하다.</p>
</div>

## 큰 그림

<MermaidDiagram
  caption="use case는 business rule을 소유하고, UoW는 transaction 경계를 소유한다. 외부 부수효과와 persistence는 각각 별도 ABC 뒤로 숨긴다."
  chart="flowchart LR; A[HTTP or CLI Input] --> B[RegisterUserUseCase]; B --> C[AbstractUnitOfWork]; C --> D[SqlAlchemyUnitOfWork]; D --> E[(Database)]; B --> F[AbstractWelcomeNotifier]; F --> G[Email or event implementation];"
/>

## 왜 `abc.ABC`를 택하나

### 이 스타일이 잘 맞는 경우

- 팀이 구조적 타이핑보다 명시적 클래스 계층을 더 읽기 편해할 때
- fake 구현도 "진짜 구현과 같은 shape"를 더 분명하게 강제하고 싶을 때
- 아키텍처 문서와 코드 리뷰에서 경계를 눈에 띄게 드러내고 싶을 때

### 그렇다고 모든 것을 ABC로 만들 필요는 없다

- 단순 내부 helper
- 바뀔 가능성이 거의 없는 concrete repository
- ORM model, DTO, dataclass value object

핵심은 "교체 가능성과 테스트 가치가 실제로 있는 경계만" 추상화하는 것이다.

## 추천 구조

```py
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Self


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class UserRead:
    id: int
    email: str
    name: str


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserModel | None: ...

    @abstractmethod
    def add(self, user: UserModel) -> None: ...


class AbstractUnitOfWork(ABC):
    @property
    @abstractmethod
    def users(self) -> AbstractUserRepository: ...

    @abstractmethod
    def __enter__(self) -> Self: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    def flush(self) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


class AbstractWelcomeNotifier(ABC):
    @abstractmethod
    def send(self, email: str, name: str) -> None: ...
```

<p class="code-caption">포인트는 use case가 "session", "engine", "SQLAlchemy model lifecycle"을 직접 모르게 두는 것이다. 대신 transaction 경계와 외부 side effect 경계만 안다.</p>

## use case는 추상 경계만 의존한다

```py
class RegisterUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractUnitOfWork],
        notifier: AbstractWelcomeNotifier,
    ) -> None:
        self.uow_factory = uow_factory
        self.notifier = notifier

    def execute(self, command: RegisterUserCommand) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(command.email) is not None:
                raise DuplicateEmail(command.email)

            record = UserModel(email=command.email, name=command.name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()

        # DB 상태가 durable해진 뒤에만 외부 부수효과를 실행한다.
        self.notifier.send(result.email, result.name)
        return result
```

## concrete SQLAlchemy 구현은 바깥에 둔다

```py
from sqlalchemy.orm import Session, sessionmaker


class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._users: SqlAlchemyUserRepository | None = None

    @property
    def users(self) -> SqlAlchemyUserRepository:
        if self._users is None:
            raise RuntimeError("unit of work not entered")
        return self._users

    def __enter__(self) -> Self:
        session = self._session_factory()
        self._session = session
        self._users = SqlAlchemyUserRepository(session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None and self._session is not None:
            self._session.rollback()
        if self._session is not None:
            self._session.close()

    def flush(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        self._session.flush()

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        self._session.commit()

    def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work not entered")
        self._session.rollback()
```

## FastAPI에서는 세션을 이렇게 주입한다

`ABC + UoW` 패턴에서 가장 중요한 wiring 포인트는 이것이다.

1. engine과 `sessionmaker`는 process scope에서 한 번 만든다.
2. request dependency는 "열린 Session"이 아니라 `sessionmaker` 또는 `uow_factory`를 공급한다.
3. 실제 `Session` 생성/종료는 `SqlAlchemyUnitOfWork.__enter__()` / `__exit__()`가 소유한다.

왜 이렇게 하느냐면, UoW가 트랜잭션 경계를 소유하는데 FastAPI dependency가 또 별도의 live `Session`을 열고 닫기 시작하면 세션 ownership이 둘로 갈라지기 때문이다.

### 1. app lifespan에서 engine과 sessionmaker를 만든다

```py
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> Iterator[None]:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    app.state.session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield
    finally:
        engine.dispose()
```

### 2. dependency는 sessionmaker와 use case를 조립한다

```py
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def get_register_user_use_case(
    session_factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    notifier: Annotated[AbstractWelcomeNotifier, Depends(get_notifier)],
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        notifier=notifier,
    )
```

### 3. route는 use case만 받는다

```py
from typing import Annotated

from fastapi import APIRouter, Depends, status

router = APIRouter()


@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterUserRequest,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
) -> UserResponse:
    result = use_case.execute(
        RegisterUserCommand(email=payload.email, name=payload.name)
    )
    return UserResponse(id=result.id, email=result.email, name=result.name)
```

<p class="code-caption">핵심은 route가 Session을 직접 모르고, dependency가 `sessionmaker -> UoW factory -> use case` 순서로 조립한다는 점이다. 이렇게 해야 UoW가 세션 수명주기와 트랜잭션 ownership을 끝까지 일관되게 가진다.</p>

## live Session을 직접 주입하는 패턴과 어떻게 다른가

### Session 직접 주입이 맞는 경우

- service가 직접 `Session`을 받고 `with session.begin():` 패턴을 쓴다
- 별도 UoW 객체를 두지 않는다
- session ownership이 service layer에서 충분히 읽힌다

### sessionmaker / UoW factory 주입이 맞는 경우

- class-based UoW가 세션 생성/종료를 소유한다
- use case가 `with self.uow_factory() as uow:` 형태로 트랜잭션 경계를 연다
- 여러 repository 묶음을 한 transaction boundary로 명시하고 싶다

즉, `UoW를 쓸 거면 live Session보다 sessionmaker/factory를 주입하는 편이 ownership이 더 깨끗하다`.

## sub-optimal -> improved: UoW를 쓰는데도 ownership이 흐려지는 경우

### 나쁜 예: use case가 Session lifecycle과 side effect 순서를 직접 짊어진다

```py
class RegisterUserUseCase:
    def __init__(self, session: Session, notifier: WelcomeNotifier) -> None:
        self.session = session
        self.notifier = notifier

    def execute(self, command: RegisterUserCommand) -> UserRead:
        repository = UserRepository(self.session)
        if repository.get_by_email(command.email) is not None:
            raise DuplicateEmail(command.email)

        record = UserModel(email=command.email, name=command.name)
        repository.add(record)
        self.session.commit()
        self.notifier.send(record.email, record.name)
        return UserRead(id=record.id, email=record.email, name=record.name)
```

<p class="code-caption">겉으로는 단순하지만, 이 use case는 session ownership, repository wiring, commit timing, side effect ordering을 동시에 안다. 이후 repository가 늘거나 테스트에서 fake를 쓰고 싶어질 때 경계가 빠르게 무너진다.</p>

### 더 나은 예: use case는 추상 경계만 알고 concrete lifecycle은 UoW가 가진다

```py
class RegisterUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractUnitOfWork],
        notifier: AbstractWelcomeNotifier,
    ) -> None:
        self.uow_factory = uow_factory
        self.notifier = notifier

    def execute(self, command: RegisterUserCommand) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(command.email) is not None:
                raise DuplicateEmail(command.email)

            record = UserModel(email=command.email, name=command.name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()

        self.notifier.send(result.email, result.name)
        return result
```

<p class="code-caption">개선 포인트는 추상화의 양이 아니라 ownership의 선명함이다. use case는 transaction boundary와 side effect boundary만 알고, session 생성/종료와 repository wiring은 concrete UoW가 맡는다.</p>

## 이 패턴에서 하지 않는 편이 좋은 것

- `get_session()`으로 live Session을 열어두고, UoW가 또 내부에서 새 Session을 만드는 것
- request dependency가 singleton UoW 인스턴스를 재사용하는 것
- use case가 `engine`이나 `Request` 객체를 직접 받게 만드는 것
- dependency 안에서 `commit()`까지 해버려서 transaction policy가 router/wiring으로 새는 것

## 테스트에서는 fake UoW가 쉬워진다

```py
class FakeUserRepository(AbstractUserRepository):
    def __init__(self) -> None:
        self.items: dict[str, UserModel] = {}

    def get_by_email(self, email: str) -> UserModel | None:
        return self.items.get(email)

    def add(self, user: UserModel) -> None:
        self.items[user.email] = user


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self._users = FakeUserRepository()
        self.committed = False

    @property
    def users(self) -> FakeUserRepository:
        return self._users

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.rollback()

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = False
```

<p class="code-caption">fake UoW가 있으면 "중복 이메일이면 commit하지 않는다", "성공 시 notifier가 한 번 호출된다" 같은 use case 규칙을 DB 없이 빠르게 검증할 수 있다.</p>

## 하지 않는 편이 좋은 것

- repository, service, use case, DTO를 전부 ABC로 만드는 것
- generic repository 하나로 모든 query shape를 숨기려는 것
- UoW가 FastAPI dependency, HTTP status code, response DTO를 알게 하는 것
- commit 전에 이메일 발송이나 이벤트 publish를 실행하는 것
- UoW 인스턴스를 singleton처럼 길게 재사용하는 것

## Code Review Lens

- use case가 정말로 transaction boundary와 external side effect boundary만 아는지 본다.
- UoW가 session 생성/종료와 repository wiring ownership을 일관되게 가지는지 본다.
- ABC가 substitution/testing 가치가 있는 경계에만 쓰였는지 본다.
- commit 이후 side effect 순서가 명시적이고 테스트 가능한지 본다.

## Common Anti-Patterns

- use case가 `Session`, `engine`, `Request`를 직접 받아 lifecycle까지 관리한다.
- live Session을 dependency에서 만들고 UoW가 또 내부에서 새 세션을 만든다.
- fake를 만들 가치가 없는 helper나 DTO까지 ABC로 추상화한다.
- notifier, publisher 같은 side effect가 commit 전에 먼저 실행된다.

## Likely Discussion Questions

- 왜 live Session보다 `uow_factory` 주입이 ownership을 더 잘 드러내는가?
- 어떤 경계는 ABC로 두고, 어떤 경계는 concrete로 남겨야 하는가?
- fake UoW 테스트와 실제 DB integration test는 각각 무엇을 검증해야 하는가?
- repository 수가 늘어날 때 UoW가 어떤 복잡성을 줄여 주고, 무엇은 줄여 주지 못하는가?

## Strong Answer Frame

- 먼저 use case가 알아야 할 최소 경계를 transaction과 side effect로 정의한다.
- 현재 구조가 session lifecycle, commit timing, fakeability를 어떻게 흐리는지 설명한다.
- UoW에 concrete lifecycle을 모으고 use case는 작은 ABC에만 의존하도록 정리한다.
- 마지막으로 fake UoW 테스트와 실제 SQLAlchemy 통합 테스트의 역할을 분리해 말한다.

## 이 저장소의 실행 예제

이 패턴은 `examples/usecase_with_uow_abc.py` 에 실행 가능한 형태로 넣어두었다.

## 같이 읽으면 좋은 페이지

- [Refactoring Atlas](/playbooks/refactoring-atlas)
- [Refactoring: Session Ownership과 Hidden Commits](/playbooks/refactoring-session-ownership-and-hidden-commits)
- [Session and Unit of Work](/sqlalchemy/session-and-unit-of-work)
- [Deployment and Engine Settings](/sqlalchemy/deployment-and-engine-settings)
- [ABC + Fake UoW Testing](/playbooks/testing-abc-and-fake-uow)
- [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)

## 공식 자료

- [abc — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
