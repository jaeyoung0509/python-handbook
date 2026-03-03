# Session and Unit of Work

<p class="lead">SQLAlchemy에서 가장 많은 버그는 `Session`을 잘못 이해해서 생긴다. Session을 "전역 캐시", "DB 연결 객체", "repository 대용"으로 여기기 시작하면 트랜잭션 경계, stale state, lazy load, 테스트 격리 문제가 연쇄적으로 터진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Session은 identity map과 unit of work를 수행하는 작업 문맥이다. repository는 session을 사용해 질의/저장을 수행하고, commit/rollback은 use case 경계에서만 다뤄야 한다.</p>
</div>

## 먼저 그림부터

<MermaidDiagram
  caption="요청 하나 또는 use case 하나가 Session 하나를 갖고, 그 안에서 repository 작업과 flush가 일어난 뒤 마지막에 commit/rollback으로 끝나는 구조가 가장 안정적이다."
  chart="flowchart LR; A[HTTP Request or Use Case] --> B[Session Scope]; B --> C[Repository Calls]; C --> D[Pending ORM State]; D --> E[flush]; E --> F[commit or rollback]; F --> G[Session Close];"
/>

## Session을 오해하는 4가지 방식

| 오해 | 실제로는 | 왜 위험한가 |
| --- | --- | --- |
| Session은 전역 캐시다 | Session은 scoped identity map이다 | scope가 길어지면 stale state와 메모리 누수가 생긴다 |
| Session은 connection이다 | 필요 시 connection을 빌려 트랜잭션을 수행한다 | connection pool과 session 수명주기를 혼동하게 된다 |
| repository마다 자기 session이 있어도 된다 | 한 use case 안 작업은 같은 session/transaction으로 묶는 편이 안전하다 | 같은 요청 안에서 commit 타이밍이 분산된다 |
| repository가 commit해도 된다 | commit은 use case 경계가 소유해야 한다 | 여러 저장 작업을 원자적으로 묶기 어려워진다 |

## 세션 수명주기 기본 패턴

```py
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "postgresql+psycopg://app:secret@localhost/app"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Iterator[Session]:
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
```

<p class="code-caption">핵심은 `sessionmaker`가 세션 생성을 담당하고, 요청 또는 작업이 끝나면 반드시 `close()`로 scope를 닫는다는 점이다. 세션을 모듈 전역 싱글턴으로 들고 있는 방식은 피해야 한다. `expire_on_commit=False`는 API 서비스에서 commit 뒤 DTO 조립이나 로깅을 할 때 예측 가능성을 높여주는 편이라 자주 선택된다.</p>

## `sessionmaker()` 기본값도 설계의 일부다

| 설정 | 권장 기본값 | 왜 자주 쓰나 | 주의할 점 |
| --- | --- | --- | --- |
| `autoflush=False` | 보통 켠다 | 조회 중 숨은 SQL이 튀는 일을 줄여준다 | `flush()` 시점을 직접 관리해야 한다 |
| `expire_on_commit=False` | API/서비스 코드에서 자주 켠다 | commit 직후 객체 접근이 덜 놀랍다 | 장기 세션을 정당화하지는 않는다 |
| `class_=Session` | 명시하는 편이 읽기 쉽다 | sync/async 팩토리 구분이 분명해진다 | async에서는 `AsyncSession` 계열을 써야 한다 |

<p class="code-caption">`autoflush=False`와 `expire_on_commit=False`는 "무조건 정답"은 아니다. 하지만 웹 API에서는 flush/commit 시점을 명시적으로 관리하고, commit 직후 응답 DTO를 만들거나 로그를 남기는 경우가 많아서 꽤 실용적인 기본값이다. 엔진과 풀 설정은 배포 형태에 따라 달라지므로 [Deployment and Engine Settings](/sqlalchemy/deployment-and-engine-settings)에서 따로 본다.</p>

## Session API를 정확히 구분하기

| API | 의미 | 언제 쓰나 | 흔한 오해 |
| --- | --- | --- | --- |
| `add(obj)` | 객체를 unit of work에 등록 | 새 ORM 객체를 저장 대상으로 넣을 때 | `add()`가 즉시 INSERT를 날린다고 오해 |
| `flush()` | 현재 pending state를 DB에 동기화 | PK가 필요하거나 FK/제약 오류를 미리 보고 싶을 때 | `flush()`가 트랜잭션 종료라고 오해 |
| `commit()` | 현재 트랜잭션 확정 | use case가 성공적으로 끝날 때 | repository 내부에서 자주 호출 |
| `rollback()` | 현재 트랜잭션 취소 | 예외 발생 후 상태를 되돌릴 때 | rollback 후 객체 상태를 신경 안 씀 |
| `refresh(obj)` | 객체를 DB 값으로 다시 읽기 | trigger/default 값을 재로딩할 때 | 모든 write 후 무조건 호출 |
| `get(Model, pk)` | PK 기준 조회, identity map 우선 활용 | 단일 엔티티 로드 | 임의 조건 조회도 `get()`으로 해결하려고 함 |
| `execute(stmt)` | statement 실행의 일반형 | Core/ORM statement를 직접 다룰 때 | ORM에서도 항상 `execute()`만 써야 한다고 생각 |
| `scalars(stmt)` | 단일 컬럼 또는 ORM 객체 스트림 | ORM select 결과를 객체 목록으로 읽을 때 | `execute()` 결과 처리와 구분 못 함 |
| `delete(obj)` | 삭제 대상으로 표시 | 엔티티 삭제 use case | 즉시 DELETE가 나간다고 생각 |
| `begin()` | 트랜잭션 context manager | write use case를 블록으로 감쌀 때 | session scope와 transaction scope를 혼동 |
| `begin_nested()` | SAVEPOINT 시작 | 테스트 격리, 부분 실패 복구 | 일반 요청 처리에 남용 |
| `close()` | 세션 scope 종료 | 요청 끝, 작업 끝 | commit과 close를 같은 것으로 오해 |

## `flush()`와 `commit()`을 분리해서 생각해야 하는 이유

```py
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_email(self, email: str) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == email)
        return self.session.scalar(stmt)

    def add(self, user: UserModel) -> None:
        self.session.add(user)


class RegisterUserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def execute(self, email: str, name: str) -> UserRead:
        with self.session.begin():
            if self.users.get_by_email(email) is not None:
                raise DuplicateEmail(email)

            record = UserModel(email=email, name=name)
            self.users.add(record)

            # INSERT를 미리 보내 PK를 확보한다.
            self.session.flush()

            return UserRead(
                id=record.id,
                email=record.email,
                name=record.name,
            )
```

<p class="code-caption">`flush()`는 SQL을 DB에 보내지만 트랜잭션을 끝내지 않는다. 위 코드는 `record.id`를 얻기 위해 flush를 호출하고, 실제 commit은 `with self.session.begin():` 블록이 정상 종료될 때 한 번만 일어난다.</p>

## 좋은 설계는 commit 위치가 다르다

### 권장

- router 또는 service 경계가 트랜잭션을 연다.
- repository는 조회/저장 로직만 가진다.
- 하나의 use case 안 여러 repository 호출이 같은 session을 공유한다.

### 비권장

- repository 메서드마다 `commit()` 한다.
- helper 함수가 내부에서 session을 새로 만든다.
- API 응답으로 ORM 객체를 직접 흘려보내서 lazy load와 serialization이 뒤섞인다.

## identity map은 "짧은 scope의 작업 메모리"에 가깝다

- 같은 Session 안에서 같은 PK의 행은 보통 같은 Python 객체로 표현된다.
- 하지만 이것은 일반적인 query cache가 아니다.
- `select(UserModel).where(UserModel.email == ...)` 같은 질의는 여전히 SQL을 보낼 수 있다.
- 따라서 Session을 장기 캐시처럼 오래 잡는 것은 이득보다 해가 크다.

## FastAPI에서 가장 안전한 패턴

```py
from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session


def get_user_service(session: Session = Depends(get_session)) -> RegisterUserService:
    return RegisterUserService(session)
```

- request마다 하나의 Session을 주입한다.
- service는 같은 session을 여러 repository에 전달한다.
- 요청이 끝나면 dependency가 session을 닫는다.

## `abc.ABC` 기반 클래스 Unit of Work 패턴

session을 직접 service에 넣는 방식은 충분히 좋다. 다만 repository 묶음이 커지고 "한 use case 안에서 어떤 저장소가 같은 transaction을 공유하는가"를 더 명시하고 싶다면 class-based Unit of Work가 읽기 좋을 때가 있다.

```py
from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker


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


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self._users: SqlAlchemyUserRepository | None = None

    @property
    def users(self) -> SqlAlchemyUserRepository:
        if self._users is None:
            raise RuntimeError("unit of work not entered")
        return self._users

    def __enter__(self) -> Self:
        session = self.session_factory()
        self.session = session
        self._users = SqlAlchemyUserRepository(session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.session is not None:
            if exc is not None:
                self.session.rollback()
            self.session.close()

    def flush(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work not entered")
        self.session.flush()

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work not entered")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("unit of work not entered")
        self.session.rollback()


class RegisterUserService:
    def __init__(
        self,
        uow_factory: Callable[[], AbstractUnitOfWork],
    ) -> None:
        self.uow_factory = uow_factory

    def execute(self, email: str, name: str) -> UserRead:
        with self.uow_factory() as uow:
            if uow.users.get_by_email(email) is not None:
                raise DuplicateEmail(email)

            record = UserModel(email=email, name=name)
            uow.users.add(record)
            uow.flush()
            result = UserRead(id=record.id, email=record.email, name=record.name)
            uow.commit()
            return result
```

<p class="code-caption">핵심은 UoW가 session과 repository 집합의 소유권을 가진다는 점이다. 서비스는 `commit()` 시점만 결정하고, session 생성/종료와 저장소 wiring은 UoW가 맡는다. 팀이 `Protocol`보다 명시적인 추상 클래스 스타일을 선호한다면 이 방식이 코드 리뷰와 런타임 실패 지점까지 더 직관적일 때가 많다. 이 저장소에는 같은 패턴을 실행 가능한 예제로 보여주는 `examples/usecase_with_uow_abc.py`도 추가했다.</p>

## 클래스 기반 UoW를 쓸 때의 기준

- 여러 repository가 항상 같은 transaction을 공유해야 할 때
- service 시그니처에 session보다 "작업 단위" 의미를 더 드러내고 싶을 때
- 팀이 구조적 타이핑보다 `abc.ABC`의 명시적 계약을 선호할 때
- 테스트에서 fake UoW를 넣어 use-case 분기를 검증하고 싶을 때

## 클래스 기반 UoW에서 하지 않는 편이 좋은 것

- UoW 내부 repository가 각자 `commit()` 하는 구조
- UoW를 long-lived singleton처럼 재사용하는 방식
- `__enter__()` 밖에서 session과 repository 속성에 접근하는 방식
- UoW가 HTTP status code나 response DTO 생성까지 알게 만드는 구조

## Session 설계 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>한 요청, 한 세션</h3>
    <p>웹 서비스에서는 request scope 세션이 기본이다. background task나 별도 worker는 자기 세션을 따로 가져야 한다.</p>
  </div>
  <div class="check-card">
    <h3>한 use case, 한 commit</h3>
    <p>commit은 business transaction이 끝나는 지점에서 한 번만 호출하는 편이 가장 읽기 쉽고 안전하다.</p>
  </div>
  <div class="check-card">
    <h3>response는 DTO로</h3>
    <p>ORM entity를 API 응답으로 직접 내보내지 말고, 응답 DTO를 명시적으로 만든다. lazy load와 schema 변화 비용을 줄일 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>테스트는 SAVEPOINT도 고려</h3>
    <p>서비스 테스트에서 빠른 롤백 격리가 필요하면 `begin_nested()` 기반 SAVEPOINT 패턴을 고려할 수 있다.</p>
  </div>
</div>

## 공식 자료

- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Transactions and Connection Management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
