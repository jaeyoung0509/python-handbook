# ABC + Fake UoW 테스트

<p class="lead">use case를 SQLAlchemy와 실제 DB까지 연결해서만 테스트하면 느리고, 실패 원인이 흐려지고, business branching보다 인프라 세부사항에 발목이 잡히기 쉽다. `abc.ABC` 기반 경계와 fake Unit of Work를 쓰면 "어떤 조건에서 commit하는가", "어떤 조건에서 외부 부수효과를 실행하는가"를 매우 빠르게 검증할 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: use case 단위 테스트에서는 `FakeUnitOfWork`와 `RecordingNotifier` 같은 fake 객체를 fixture로 만들어 business branching을 검증하고, Session/flush/loading strategy/제약조건은 integration test로 올린다. fake는 transaction semantics를 흉내 내는 도구이지, SQLAlchemy를 대체하는 도구가 아니다.</p>
</div>

## fixture graph를 먼저 본다

<MermaidDiagram
  caption="unit test에서도 자원 그래프가 읽혀야 한다. use case는 fake UoW와 fake notifier를 받고, pytest fixture가 그 graph를 조립한다."
  chart="flowchart TB; A[uow fixture] --> C[use_case fixture]; B[notifier fixture] --> C; C --> D[test body];"
/>

## fake UoW 테스트가 잡아주는 것

- 중복 이메일이면 commit하지 않는가
- 성공 시 notifier가 정확히 한 번 호출되는가
- commit 후 side effect 순서가 유지되는가
- use case가 SQLAlchemy 세부 구현에 직접 묶이지 않았는가

## fake UoW 테스트가 잡아주지 못하는 것

- 실제 `Session.flush()` / `commit()` 동작
- ORM mapping, relationship loading, constraint error
- DB isolation level, transaction boundary, lock contention
- query count, N+1, lazy load 문제

이 네 가지는 integration test나 실제 SQLAlchemy 예제로 올려야 한다.

## 추천 구조

```py
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from types import TracebackType
from typing import Self


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    name: str


class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> UserRecord | None: ...

    @abstractmethod
    def add(self, user: UserRecord) -> None: ...


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
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
```

## pytest fixture는 graph를 조립만 한다

```py
import pytest


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def use_case(
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        uow_factory=lambda: uow,
        notifier=notifier,
    )
```

<p class="code-caption">이 구조의 장점은 test body가 조립 코드를 반복하지 않는다는 점이다. 자원 graph는 fixture에 있고, 테스트는 그 graph를 소비해 rule만 검증한다.</p>

## 성공 / 실패 테스트를 분리한다

```py
def test_register_user_commits_and_notifies(
    use_case: RegisterUserUseCase,
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> None:
    result = use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))

    assert result.email == "neo@example.com"
    assert uow.committed is True
    assert notifier.calls == [("neo@example.com", "Neo")]


def test_duplicate_email_rolls_back_and_skips_notification(
    use_case: RegisterUserUseCase,
    uow: FakeUnitOfWork,
    notifier: RecordingNotifier,
) -> None:
    uow.users.add(UserRecord(email="neo@example.com", name="Neo"))

    with pytest.raises(DuplicateEmail):
        use_case.execute(RegisterUserCommand(email="neo@example.com", name="Neo"))

    assert uow.committed is False
    assert uow.rolled_back is True
    assert notifier.calls == []
```

## `monkeypatch`는 어디서 쓰나

- 환경 변수 테스트
- 전역 함수/시간/UUID 같은 외부 read
- import 시점 부수효과 차단

반대로, 이미 `ABC` 뒤에 fake object를 넣을 수 있다면 `monkeypatch`보다 fake 객체가 더 읽기 좋다. fake는 명시적 계약을 유지하고, monkeypatch는 이름 교체 중심이라 구조가 덜 드러난다.

## 언제 integration test로 올려야 하나

### fake UoW로 충분한 경우

- business branch
- commit 여부
- side effect 호출 여부
- domain error 매핑

### integration test가 필요한 경우

- unique constraint 실제 동작
- `flush()` 후 PK 생성
- relationship loading
- transaction rollback과 DB 상태 확인

## 이 저장소의 예제

- 단위 테스트 예제: `tests/test_abc_fake_uow_pytest.py`
- 경계 설계 설명: [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)
- DB가 들어간 fixture 예제: `tests/test_fastapi_fixtures_and_teardown.py`

## 하지 않는 편이 좋은 것

- fake UoW 하나로 SQLAlchemy 동작까지 다 검증하려는 것
- 테스트마다 use case 조립 코드를 복붙하는 것
- notifier를 `monkeypatch`로 숨겨서 호출 기록이 어디 있는지 흐리게 만드는 것
- unit test와 integration test 역할을 섞어 assertion을 과하게 늘리는 것

## 공식 자료

- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [abc — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
