# Refactoring Fat Routes and Dependency Leakage

<p class="lead">fat route와 dependency leakage는 보통 같이 나타난다. route는 원래 transport adapter여야 하고 dependency는 resource wiring이어야 하는데, 둘이 무너지기 시작하면 validation, auth, policy, query, commit, serialization이 한 request path에 엉킨다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 이 냄새를 고칠 때 가장 안전한 순서는 "route에서 business branching 제거 -> dependency를 boring하게 되돌리기 -> service/use case에 action ownership 모으기"다. 처음부터 전체 폴더 구조를 갈아엎을 필요는 없다.</p>
</div>

## 1) sub-optimal snippet

```py
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_checkout_service(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> "CheckoutService":
    if os.getenv("CHECKOUT_DISABLED", "false") == "true":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    service = CheckoutService(session)
    await service.prepare_cart_for(user.user_id)
    await session.commit()
    return service


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> CheckoutResponse:
    if payload.total <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    existing = await session.scalar(
        select(OrderRecord).where(OrderRecord.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        return CheckoutResponse.model_validate(existing)

    if user.plan == "free" and payload.total > 100:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    record = OrderRecord(user_id=user.user_id, total=payload.total)
    session.add(record)
    await session.commit()
    return CheckoutResponse.model_validate(record)
```

## 2) 정확한 냄새는 무엇인가

- route가 HTTP parsing을 넘어 business branching과 transaction policy까지 소유한다.
- dependency가 resource wiring을 넘어 policy branching과 side effect까지 수행한다.
- settings/env lookup, idempotency query, commit, DTO 조립이 한 request path에 섞여 있다.

이 구조는 작을 때는 빨라 보이지만, 이후 timeout, tracing, audit log, retry, feature flag가 붙기 시작하면 수정 반경이 route와 dependency 전체로 번진다.

## 3) 가장 작은 안전한 리팩터링 순서

1. route에서 business branching과 commit을 service 메서드로 이동한다.
2. dependency는 session/settings/principal을 조립하는 선으로 축소한다.
3. HTTP 에러는 domain error나 policy result를 route에서 매핑하거나 exception handler로 보낸다.
4. route는 request DTO -> command 변환과 response DTO 반환만 남긴다.

포인트는 "새 레이어를 많이 만드는 것"이 아니라 ownership을 한 번에 하나씩 되돌리는 것이다.

## 4) improved end state

```py
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_checkout_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    principal: Annotated[CurrentUser, Depends(get_current_user)],
) -> "CheckoutService":
    return CheckoutService(
        session=session,
        settings=settings,
        principal=principal,
    )


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutRequest,
    service: Annotated["CheckoutService", Depends(get_checkout_service)],
) -> CheckoutResponse:
    command = CheckoutCommand(
        idempotency_key=payload.idempotency_key,
        total=payload.total,
    )
    return await service.checkout(command)


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

    async def checkout(self, command: CheckoutCommand) -> CheckoutResponse:
        if not self.settings.checkout_enabled:
            raise CheckoutDisabled()
        if self.principal.is_suspended:
            raise PermissionDenied()
        if self.principal.plan == "free" and command.total > 100:
            raise PlanLimitExceeded()

        existing = await self.session.scalar(
            select(OrderRecord).where(OrderRecord.idempotency_key == command.idempotency_key)
        )
        if existing is not None:
            return CheckoutResponse.model_validate(existing)

        record = OrderRecord(user_id=self.principal.user_id, total=command.total)
        self.session.add(record)
        await self.session.commit()
        return CheckoutResponse.model_validate(record)
```

## 5) 무엇이 좋아지나

- `tests`: route는 transport contract만, service는 business branching만 테스트하면 된다.
- `operations`: tracing, timeout, audit log를 route/service 어디에 둘지 더 명확해진다.
- `change isolation`: policy나 settings 변화가 HTTP wiring 전체를 흔들지 않는다.

## Code Review Lens

- route가 request parsing, auth boundary, response contract만 알고 있는지 본다.
- dependency가 resource wiring만 하고 branching과 commit은 하지 않는지 본다.
- service/use case가 business action 하나를 대표하는지 본다.
- settings lookup과 principal restoration이 explicit input으로 들어오는지 본다.

## Common Anti-Patterns

- dependency가 feature flag를 읽고 HTTP 예외까지 직접 던진다.
- route가 domain branching, query, commit, response assembly를 모두 수행한다.
- `async` endpoint 안에 sync client 호출이나 sync secret lookup을 숨긴다.
- fat route를 고치겠다며 처음부터 모든 endpoint를 대규모 구조 변경에 태운다.

## Likely Discussion Questions

- 어떤 책임부터 route 밖으로 빼는 것이 가장 안전한가?
- dependency를 boring하게 만든다는 말은 정확히 무엇을 남기고 무엇을 빼는 것인가?
- exception handler와 domain error를 어느 시점에 도입하는 것이 좋은가?
- service 경계를 잘 잡으면 background worker나 CLI 재사용에 어떤 이점이 생기는가?

## Strong Answer Frame

- 먼저 route와 dependency에 섞인 책임을 boundary 기준으로 분류한다.
- 그 다음 가장 작은 이동 단위로 business branching과 commit ownership을 안쪽으로 옮긴다.
- HTTP concern과 application concern이 분리되면 테스트와 운영 가시성이 어떻게 좋아지는지 연결한다.
- 마지막으로 필요하면 exception handler, outbox, audit log 같은 다음 단계 확장을 언급한다.

## 같이 읽으면 좋은 문서

- [Refactoring Atlas](/playbooks/refactoring-atlas)
- [Project Structure](/fastapi/project-structure)
- [Dependency Injection](/fastapi/dependency-injection)
- [API Service Template](/playbooks/api-service-template)
