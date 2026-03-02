# Lifespan and Testing

<p class="lead">FastAPI 서비스는 "요청 처리 코드"만 맞아서는 충분하지 않다. DB engine, HTTP client, cache client, settings, background task runner 같은 자원을 언제 열고 언제 닫는지까지 설계해야 production과 test가 같은 모델로 움직인다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: startup/shutdown 이벤트를 흩뿌리기보다 lifespan에서 자원 소유권을 명확히 두고, 테스트는 같은 lifespan 경계를 통과하도록 만드는 편이 가장 일관된다. 테스트에서 dependency override와 transaction 격리를 같이 설계해야 "실제 서비스와 비슷한 테스트"가 된다.</p>
</div>

## 먼저 그림으로 잡기

<MermaidDiagram
  caption="애플리케이션 수명주기와 요청 수명주기는 다르다. 무거운 공유 자원은 app lifespan에, request scope 자원은 dependency에 두는 것이 기본이다."
  chart="flowchart LR; A[App startup] --> B[Lifespan opens shared resources]; B --> C[Requests arrive]; C --> D[Request dependency opens session]; D --> E[Service and handler work]; E --> F[Dependency cleanup closes session]; F --> G[App shutdown]; G --> H[Lifespan closes engine, clients, caches];"
/>

## Lifespan은 무엇을 소유해야 하나

### lifespan에 두기 좋은 것

- SQLAlchemy engine 또는 async engine
- `httpx.AsyncClient` 같은 프로세스 공유 클라이언트
- Redis client, message broker producer
- warm-up이 필요한 설정/모델/캐시

### request dependency에 두기 좋은 것

- `Session` / `AsyncSession`
- 현재 사용자 principal
- 요청 단위 trace context
- 요청 단위 서비스 인스턴스

## 권장 패턴: app state + dependency 분리

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_async_engine(
        "postgresql+asyncpg://app:secret@localhost/app",
        pool_pre_ping=True,
    )
    app.state.session_factory = async_sessionmaker(
        engine,
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(lifespan=lifespan)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
```

<p class="code-caption">engine는 process-wide 자원이라 lifespan에서 열고 닫는다. 반면 `AsyncSession`은 request마다 새로 만들어야 한다. app state는 공유 자원을 보관하는 곳이지, request마다 mutate되는 비즈니스 상태를 넣는 곳이 아니다.</p>

## 테스트에서도 lifespan을 통과시켜야 하는 이유

`TestClient(app)` 또는 ASGI transport 기반 통합 테스트를 context manager로 열면 lifespan이 같이 실행된다. 이 과정을 생략하면 production에서는 생성되는 자원이 테스트에서는 비어 있어서, 테스트가 잘못된 전제 위에서 돌아갈 수 있다.

```py
from fastapi.testclient import TestClient


def test_healthcheck() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
```

## dependency override는 "mock 주입"보다 boundary 검증 도구다

```py
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_test_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = get_test_session
```

- unit test에서는 fake service를 주입해 route contract를 빠르게 검증할 수 있다.
- integration test에서는 실제 DB 세션 factory를 주입하되 rollback 전략을 붙일 수 있다.
- override는 테스트가 끝나면 원래 dependency로 복원해야 한다.

## 비동기 통합 테스트 기본 패턴

```py
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_register_user() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/users",
            json={"email": "neo@example.com", "name": "Neo"},
        )

    assert response.status_code == 201
    assert response.json()["email"] == "neo@example.com"
```

## DB 테스트를 설계할 때 체크할 것

| 질문 | 권장 방향 | 피해야 할 패턴 |
| --- | --- | --- |
| 테스트마다 DB를 어떻게 초기화하나 | fixture에서 schema 준비 또는 transaction rollback | 각 테스트가 스스로 migration을 반복 |
| 세션 격리는 어떻게 보장하나 | SAVEPOINT, 별도 test DB, deterministic seed | global session 재사용 |
| 서비스는 무엇을 검증하나 | status code뿐 아니라 response shape와 side effect | route 함수 내부 구현 세부사항 |
| 외부 API는 어떻게 대체하나 | override된 client/provider 주입 | 실제 production endpoint 호출 |

## 흔한 실수

- startup에서 session을 만들어 전역으로 재사용한다.
- 테스트가 lifespan을 거치지 않아 app state 초기화가 빠진다.
- `dependency_overrides`를 테스트 후 정리하지 않는다.
- 비동기 테스트에서 sync client, sync fixture, event loop lifecycle이 뒤섞인다.

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>공유 자원은 lifespan</h3>
    <p>engine, HTTP client, cache client처럼 process 범위 자원은 lifespan에 둬야 열고 닫는 위치가 명확하다.</p>
  </div>
  <div class="check-card">
    <h3>요청 자원은 dependency</h3>
    <p>세션과 현재 사용자 같은 request scope 정보는 `yield` dependency로 관리하는 편이 가장 읽기 쉽다.</p>
  </div>
  <div class="check-card">
    <h3>테스트도 같은 경계 사용</h3>
    <p>lifespan, dependency override, DB rollback 전략을 production과 최대한 같은 구조 위에 올린다.</p>
  </div>
  <div class="check-card">
    <h3>외부 의존성은 교체 가능해야 함</h3>
    <p>서비스가 구체 구현을 직접 만들지 않고 provider로 받도록 설계해야 테스트 override가 쉬워진다.</p>
  </div>
</div>

## 공식 자료

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
