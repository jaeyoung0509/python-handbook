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

## sub-optimal -> improved: dependency가 business layer가 되는 경우

### 나쁜 예: dependency가 분기와 commit 정책까지 소유

```py
import os

from fastapi import Depends, HTTPException, status


async def get_checkout_service(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> CheckoutService:
    if os.getenv("CHECKOUT_DISABLED", "false") == "true":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    service = CheckoutService(session)
    await service.prepare_cart_for(user.user_id)
    await session.commit()
    return service
```

<p class="code-caption">이 dependency는 configuration lookup, policy branching, service side effect, commit까지 품는다. 이렇게 되면 DI가 framework wiring이 아니라 숨은 business layer가 되고, override/test도 지나치게 비싸진다.</p>

### 더 나은 예: dependency는 wiring만 한다

```py
from typing import Annotated

from fastapi import Depends


def get_checkout_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[CurrentUser, Depends(get_current_user)],
) -> CheckoutService:
    return CheckoutService(
        session=session,
        settings=settings,
        principal=principal,
    )


class CheckoutService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        principal: CurrentUser,
    ) -> None:
        self.session = session
        self.settings = settings
        self.principal = principal

    async def checkout(self, command: CheckoutCommand) -> CheckoutResult:
        if not self.settings.checkout_enabled:
            raise CheckoutDisabled()
        if self.principal.is_suspended:
            raise PermissionDenied()
        ...
```

<p class="code-caption">개선의 핵심은 dependency를 boring하게 만드는 것이다. 자원 조립은 DI가 하고, business branching과 transaction policy는 service/use case가 읽히는 곳으로 남긴다.</p>

## 실전 규칙

- dependency는 "리소스 공급자"이지 "비즈니스 계층"이 아니다.
- request scope 자원은 `yield` dependency로 닫힘을 보장한다.
- service는 dependency에서 조립할 수 있지만, business branching은 service 메서드 안에 둔다.
- background task, scheduler, CLI는 FastAPI dependency 바깥에서 별도 session lifecycle을 가져야 한다.

## Code Review Lens

- dependency가 session, settings, principal, client 같은 자원을 조립하는 선에서 멈추는지 본다.
- `yield` dependency가 request-scoped resource cleanup을 실제로 보장하는지 본다.
- service 생성과 business branching이 구분돼 있는지 본다.
- FastAPI 타입이 service/use case 시그니처 안으로 새지 않는지 본다.

## Common Anti-Patterns

- dependency 안에서 feature flag를 읽고 HTTP 에러까지 직접 결정한다.
- dependency가 `commit()` 또는 외부 API 호출을 먼저 실행해버린다.
- CLI, scheduler, background worker가 FastAPI dependency lifecycle에 기대어 session을 쓴다.
- 자원 공급과 권한 정책, 도메인 규칙을 한 dependency 체인에 욱여넣는다.

## Likely Discussion Questions

- 어떤 로직까지 dependency에 두고, 어디서부터 service로 넘길 것인가?
- `yield` dependency가 빠졌을 때 connection/session leak는 어떤 형태로 나타나는가?
- 테스트 override를 값 교체 수준으로 유지하려면 dependency shape를 어떻게 설계해야 하는가?
- background job에서도 같은 service를 쓰고 싶다면 FastAPI DI와 어떤 선에서 분리해야 하는가?

## Strong Answer Frame

- dependency의 책임을 resource ownership과 boundary wiring으로 먼저 정의한다.
- 현재 구조에서 business logic가 DI에 스며들었을 때 생기는 테스트/운영 문제를 짚는다.
- cleanup이 필요한 자원과 아닌 자원을 구분해 `yield` 여부를 결정한다.
- 마지막으로 HTTP, CLI, worker에서 같은 service를 재사용할 수 있는지로 설계를 검증한다.

## 공식 자료

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
