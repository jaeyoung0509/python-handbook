# Use Case + UoW + Interface

<p class="lead">이 페이지는 "SOLID를 고려한 설계"를 실제 Python 서비스 코드로 번역하는 방법을 보여준다. 핵심은 모든 것을 인터페이스로 감싸는 것이 아니라, use case가 진짜로 바깥에 의존하는 경계만 추상화하고, SQLAlchemy 같은 인프라 구현은 concrete로 남기는 것이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: use case는 `Protocol` 기반의 작은 경계에 의존하고, SQLAlchemy Unit of Work는 concrete implementation으로 둔다. DIP는 "모든 것을 interface로 만들기"가 아니라, 테스트와 교체 가능성이 실제로 필요한 경계에만 추상화를 두는 것이다.</p>
</div>

## 큰 그림

<MermaidDiagram
  caption="use case는 transaction 경계와 외부 부수효과 경계를 조합한다. UoW는 DB 작업 단위를 소유하고, notifier 같은 외부 의존성은 별도 interface로 분리하는 편이 깔끔하다."
  chart="flowchart LR; A[HTTP or CLI Input] --> B[Use Case]; B --> C[UnitOfWork Protocol]; C --> D[SqlAlchemyUnitOfWork]; D --> E[(Database)]; B --> F[Notifier Protocol]; F --> G[Email or event implementation];"
/>

## 어떤 경계를 인터페이스로 둘 것인가

### 보통 인터페이스로 둘 가치가 큰 것

- 외부 부수효과: email, queue publish, payment gateway
- use case가 직접 필요로 하는 작업 단위 경계
- 테스트에서 fake로 대체하고 싶은 포트(port)

### 굳이 인터페이스로 둘 필요가 적은 것

- 단순 CRUD helper
- 앱 내부에서 바뀔 가능성이 거의 없는 concrete repository
- SQLAlchemy model 자체

## 추천 구조

```py
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


@dataclass(frozen=True, slots=True)
class UserRead:
    id: int
    email: str
    name: str


class UserRepositoryPort(Protocol):
    def get_by_email(self, email: str) -> UserModel | None: ...
    def add(self, user: UserModel) -> None: ...


class UnitOfWorkPort(Protocol):
    users: UserRepositoryPort

    def __enter__(self) -> "UnitOfWorkPort": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def flush(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class WelcomeNotifier(Protocol):
    def send(self, email: str, name: str) -> None: ...
```

## use case는 interface에만 의존한다

```py
class RegisterUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWorkPort],
        notifier: WelcomeNotifier,
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

<p class="code-caption">중요한 포인트는 외부 부수효과를 commit 뒤로 미룬다는 점이다. 메일 발송이나 이벤트 publish를 transaction 안에서 먼저 해버리면 DB rollback과 외부 세계 상태가 어긋날 수 있다.</p>

## concrete SQLAlchemy 구현은 이렇게 둔다

```py
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self.users: SqlAlchemyUserRepository | None = None

    def __enter__(self) -> Self:
        session = self.session_factory()
        self.session = session
        self.users = SqlAlchemyUserRepository(session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None and self.session is not None:
            self.session.rollback()
        if self.session is not None:
            self.session.close()

    def flush(self) -> None:
        assert self.session is not None
        self.session.flush()

    def commit(self) -> None:
        assert self.session is not None
        self.session.commit()

    def rollback(self) -> None:
        assert self.session is not None
        self.session.rollback()
```

## 이 패턴이 좋은 이유

- use case는 SQLAlchemy 세부사항에 직접 묶이지 않는다.
- UoW는 transaction과 repository wiring을 한 객체로 묶는다.
- notifier 같은 외부 부수효과는 fake로 바꿔 테스트하기 쉽다.
- interface 개수는 적고 의미는 분명하다.

## 하지 않는 편이 좋은 것

- repository, service, use case, DTO 전부를 interface로 만드는 것
- generic repository 하나로 모든 query shape를 숨기려는 것
- UoW가 HTTP status code나 FastAPI dependency를 아는 것
- commit 전에 외부 side effect를 실행하는 것
- port 이름만 있고 실제 교체 가능성이 없는 추상화를 남발하는 것

## 이 저장소의 실행 예제

이 패턴은 `examples/usecase_with_uow_interfaces.py` 에 실행 가능한 형태로 넣어두었다.

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>use case는 port에 의존</h3>
    <p>DB 구현 상세와 외부 부수효과 구현은 use case 바깥으로 민다.</p>
  </div>
  <div class="check-card">
    <h3>UoW는 transaction 소유</h3>
    <p>session 생성, repository wiring, rollback/close 책임을 한 객체로 묶는다.</p>
  </div>
  <div class="check-card">
    <h3>commit 후 side effect</h3>
    <p>이메일, 이벤트 publish는 DB commit 뒤로 미루는 편이 데이터 일관성에 유리하다.</p>
  </div>
  <div class="check-card">
    <h3>추상화는 필요한 곳만</h3>
    <p>DIP는 계층마다 interface를 강제하는 규칙이 아니라, 교체 가능성이 실제 필요한 경계에만 쓰는 도구다.</p>
  </div>
</div>

## 공식 자료

- [Python typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
