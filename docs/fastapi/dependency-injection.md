# Dependency Injection

<p class="lead">FastAPI의 DI는 단순히 `Depends`를 쓰는 문법이 아니라, 요청 수명주기 안에서 세션, 설정, 인증 주체, 외부 클라이언트를 어디서 생성하고 어디서 닫을지 결정하는 wiring 레이어다. 여기서 책임이 흐려지면 비즈니스 코드가 프레임워크에 잠식된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: dependency는 리소스 wiring과 경계 연결만 해야 한다. 비즈니스 로직, commit 정책, 응답 shape 결정은 service와 schema 레이어에 남겨두는 편이 가장 오래 간다.</p>
</div>

## 의존성 그래프를 이렇게 본다

<MermaidDiagram
  caption="dependency는 요청마다 필요한 리소스를 연결하지만, 트랜잭션 정책과 도메인 규칙까지 품으면 안 된다."
  chart="flowchart LR; A[Request] --> B[Router]; B --> C[Depends(get_session)]; B --> D[Depends(get_current_user)]; C --> E[Session]; E --> F[Service]; D --> F; F --> G[Response DTO];"
/>

## 가장 중요한 패턴: yield dependency

```py
from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(session)
```

<p class="code-caption">`yield` dependency는 세션처럼 "열고 닫아야 하는 자원"에 가장 적합하다. 반면 service 생성은 자원 정리가 필요 없는 얇은 wiring이므로 일반 함수로 두는 편이 읽기 쉽다.</p>

## DI에 넣어도 되는 것과 넣지 말아야 하는 것

| dependency에 넣어도 되는 것 | service로 남겨야 하는 것 |
| --- | --- |
| DB session 생성/정리 | business rule |
| 설정 객체 | commit 시점 결정 |
| 인증 principal 추출 | 도메인 검증 |
| 외부 API client lifecycle | 응답 DTO 조립 규칙 |

## 테스트 override도 설계의 일부다

```py
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_test_session() -> AsyncIterator[AsyncSession]:
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_session] = get_test_session
```

## 실전 규칙

- dependency는 "리소스 공급자"이지 "비즈니스 계층"이 아니다.
- request scope 자원은 `yield` dependency로 닫힘을 보장한다.
- service는 dependency에서 조립할 수 있지만, business branching은 service 메서드 안에 둔다.
- background task, scheduler, CLI는 FastAPI dependency 바깥에서 별도 session lifecycle을 가져야 한다.

## 공식 자료

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
