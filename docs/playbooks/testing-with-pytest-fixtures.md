# Testing with Fixtures

<p class="lead">좋은 테스트는 assert 문 몇 줄이 아니라 fixture 경계 설계에서 갈린다. DB, FastAPI app, dependency override, TestClient, 외부 API stub을 어떻게 열고 닫는지 흐려지면 테스트는 금방 느리고 flaky하며 서로 간섭하기 시작한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: pytest에서는 `yield fixture`를 기본으로 삼고, teardown은 fixture 바로 아래에 둔다. app, DB, client, override를 분리해 fixture graph를 명확히 만들고, 테스트는 그 조합을 소비만 하게 만드는 편이 가장 오래 간다.</p>
</div>

## fixture graph를 먼저 본다

<MermaidDiagram
  caption="테스트에서도 자원 수명주기는 의존성 그래프로 읽히는 편이 좋다. 바깥 자원이 먼저 열리고, 안쪽 fixture가 그것을 소비한 뒤 역순으로 teardown된다."
  chart="flowchart TB; A[engine fixture] --> B[session_factory fixture]; B --> C[app fixture]; C --> D[client fixture]; B --> E[seed data fixture]; D --> F[test body]; E --> F;"
/>

## 기본 규칙

- fixture는 자원을 만든다.
- 테스트 함수는 자원을 조합해 동작을 검증한다.
- teardown은 `yield` 바로 아래에 둔다.
- global mutable state를 테스트끼리 공유하지 않는다.

## 가장 읽기 좋은 패턴

```py
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: TestSettings()
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
```

<p class="code-caption">중요한 점은 teardown이 fixture 정의 바로 옆에 있다는 것이다. `dependency_overrides.clear()` 같은 정리 코드를 test body 밖으로 빼두면 누가 자원을 닫는지 읽기가 쉬워진다.</p>

## DB fixture는 격리 전략을 명시해야 한다

### 작은 서비스 / 시작 단계

- function-scoped SQLite
- 테스트마다 schema 생성/삭제
- 느리더라도 단순해서 읽기 좋다

### 더 큰 서비스

- connection + transaction + rollback
- 필요하면 nested SAVEPOINT
- 테스트 속도와 격리를 동시에 노릴 수 있다

## `yield fixture`가 기본인 이유

pytest 공식 문서도 teardown/finalization 기본 패턴으로 `yield fixture`를 먼저 권장한다. `addfinalizer()`는 teardown 대상을 동적으로 등록해야 할 때 유용하지만, 일상적인 서비스 테스트에서는 `yield`가 더 읽기 쉽고 안전하다.

`ABC + Fake UoW` 단위 테스트 패턴은 [ABC + Fake UoW Testing](/playbooks/testing-abc-and-fake-uow)에서 별도로 더 깊게 다룬다.

## 하지 않는 편이 좋은 것

- giant `autouse` fixture 하나에 모든 setup을 몰아넣는다.
- 테스트 함수 안에서 `dependency_overrides`를 직접 만지고 정리하지 않는다.
- session이나 client를 모듈 전역으로 재사용한다.
- fixture가 무엇을 cleanup하는지 숨긴다.
- 외부 API stub과 DB seed를 하나의 fixture에 섞는다.

## 실전 테스트 레이아웃 예

```text
tests/
  conftest.py
  integration/
    test_users_api.py
  unit/
    test_user_service.py
```

- `conftest.py`: 공용 fixture
- `integration/`: HTTP contract, DB, serialization
- `unit/`: 순수 service/domain logic

## 이 저장소의 예제

이 저장소에는 `tests/test_fastapi_fixtures_and_teardown.py` 파일을 추가했다. 다음 패턴을 보여준다.

- engine fixture 생성과 teardown
- seed fixture
- `dependency_overrides` 설치와 cleanup
- `TestClient` context manager teardown

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>fixture가 자원 소유권을 가진다</h3>
    <p>누가 열고 누가 닫는지 fixture만 봐도 읽혀야 한다.</p>
  </div>
  <div class="check-card">
    <h3>override cleanup이 있다</h3>
    <p>FastAPI dependency override는 반드시 fixture teardown에서 정리한다.</p>
  </div>
  <div class="check-card">
    <h3>DB 격리 전략이 명시적이다</h3>
    <p>schema recreate인지 rollback인지 팀 기준이 있어야 flaky test가 줄어든다.</p>
  </div>
  <div class="check-card">
    <h3>autouse는 최소화한다</h3>
    <p>숨은 fixture는 테스트 읽기를 어렵게 하므로 공통 인프라에만 제한적으로 쓴다.</p>
  </div>
</div>

## 공식 자료

- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest fixture finalization](https://docs.pytest.org/en/stable/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
