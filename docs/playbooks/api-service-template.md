# API Service Template

<p class="lead">작은 FastAPI 프로젝트는 금방 시작할 수 있지만, 몇 주만 지나도 route 함수에 validation, transaction, logging, ORM, 외부 API 호출이 한데 엉키기 쉽다. 이 문서는 "처음부터 완벽한 아키텍처"보다, 가장 덜 후회하는 기본 구조를 제안한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 서비스의 핵심은 계층 수를 많이 만드는 것이 아니라 경계를 분명히 두는 것이다. route는 transport adapter, service는 use-case orchestration, repository는 persistence detail, schema는 외부 계약, settings/logging/lifespan은 infrastructure boundary로 두면 대부분의 복잡성이 정리된다.</p>
</div>

## 추천 구조 한 장 요약

<MermaidDiagram
  caption="HTTP, application, persistence, infrastructure 경계를 나누면 FastAPI 서비스가 커져도 책임 이동 경로가 비교적 명확하다."
  chart="flowchart LR; A[Router and DTOs] --> B[Service or Use Case]; B --> C[Repository]; C --> D[Session and Database]; A --> E[Auth and Dependency Wiring]; E --> B; F[Settings and Lifespan] --> E; F --> D;"
/>

## 폴더 구조 추천

```text
app/
  api/
    routes/
      users.py
      health.py
  schemas/
    user.py
  services/
    user_service.py
  repositories/
    user_repository.py
  db/
    models.py
    session.py
  domain/
    errors.py
  core/
    config.py
    logging.py
  main.py
tests/
  integration/
  unit/
```

## 각 레이어는 무엇을 알아야 하나

| 레이어 | 책임 | 알면 안 되는 것 |
| --- | --- | --- |
| route | HTTP 입력/출력, auth, status code, response model | ORM 세부 구현, commit 정책 |
| schema | request/response 계약 | DB 세션, 외부 API 호출 |
| service | business action orchestration, transaction boundary | HTTP framework 세부사항 |
| repository | query shape, persistence detail | HTTP status, serialization 계약 |
| core/infra | settings, logging, lifespan, clients | business branching |

## 앱 진입점은 wiring만 한다

```py
from fastapi import FastAPI

from app.api.routes import health, users
from app.core.config import Settings, get_settings
from app.db.session import lifespan


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(users.router)
    return app


app = create_app()
```

<p class="code-caption">`main.py`는 business logic가 아니라 wiring entrypoint다. route 등록, 설정 로딩, lifespan 연결까지가 주된 책임이고, 도메인 규칙을 여기로 끌어올리지 않는 편이 좋다.</p>

## 설정과 로깅도 경계다

- `BaseSettings` 또는 설정 provider는 앱 시작 시점에만 읽고, 서비스 코드 전체가 환경 변수를 직접 읽지 않게 한다.
- 로깅은 route마다 직접 `logger = ...`로 찍기보다 request id, domain event, error boundary 전략을 먼저 정한다.
- settings 객체는 dependency나 app factory를 통해 주입하는 편이 테스트에 유리하다.

`settings.py`와 `pydantic-settings`를 어떤 기준으로 설계할지는 [Settings and Pydantic Settings](/playbooks/settings-and-pydantic-settings)에서, 배포 대상을 어떻게 고를지는 [Lambda vs Kubernetes](/playbooks/lambda-vs-kubernetes)에서 더 깊게 다룬다.

## 테스트 구조도 처음부터 나눠둔다

### unit test

- 순수 business rule
- service method의 분기
- typing boundary와 serializer 로직

### integration test

- HTTP contract
- dependency override
- DB session lifecycle
- 실제 serialization 결과

## "잘 커지는" 서비스의 규칙

1. route는 얇게 유지한다.
2. commit은 service/use-case 경계에서만 일어난다.
3. ORM entity는 내부 구현이고, 응답은 DTO로 끝낸다.
4. background 작업과 request path를 분리한다.
5. observability와 timeout을 early default로 넣는다.

## sub-optimal -> improved: 서비스 뼈대에서 가장 먼저 무너지는 지점

### 나쁜 예: route, 설정, persistence, side effect가 한 덩어리

```py
import os

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.post("/orders")
async def create_order(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_session),
) -> OrderRead:
    if os.getenv("ALLOW_ORDERING", "true") != "true":
        raise HTTPException(status_code=503, detail="ordering disabled")

    order = OrderModel.model_validate(payload)
    session.add(order)
    await session.commit()
    await publish_order_created(order.id)
    return OrderRead.model_validate(order)
```

<p class="code-caption">이 구조는 작을 때는 빨라 보이지만, ordering policy, transaction 경계, 이벤트 발행 순서, DTO 안정성이 모두 route 파일에 묶인다. 이후 retry, timeout, idempotency, audit logging을 붙일수록 route가 서비스 전체를 대표하는 giant function이 된다.</p>

### 더 나은 예: route는 transport, service는 action orchestration

```py
@router.post("/orders", response_model=OrderRead)
async def create_order(
    payload: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    command = CreateOrderCommand.model_validate(payload)
    return await service.create_order(command)


class OrderService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        publisher: OrderPublisher,
    ) -> None:
        self.session = session
        self.settings = settings
        self.publisher = publisher

    async def create_order(self, command: CreateOrderCommand) -> OrderRead:
        if not self.settings.allow_ordering:
            raise OrderingDisabled()

        order = OrderModel.from_command(command)
        self.session.add(order)
        await self.session.commit()
        await self.publisher.publish_created(order.id)
        return OrderRead(id=order.id, status=order.status)
```

<p class="code-caption">핵심은 layer를 늘리는 것이 아니라 ownership을 읽히게 만드는 것이다. route는 transport adapter, service는 business action, settings/publisher는 injected boundary가 되면 리팩터링과 장애 대응이 훨씬 덜 꼬인다.</p>

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>엔트리포인트는 wiring 전용</h3>
    <p>앱 생성 함수는 설정과 router 연결을 담당하고, 도메인 규칙을 직접 품지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>service가 트랜잭션 소유</h3>
    <p>repository 내부 commit을 피하고, business action 단위로 transaction을 닫는다.</p>
  </div>
  <div class="check-card">
    <h3>테스트 경계가 코드 경계와 같아야 함</h3>
    <p>lifespan, dependency override, DB rollback 전략을 테스트에서도 같은 구조로 재사용한다.</p>
  </div>
  <div class="check-card">
    <h3>settings와 logging도 설계 대상</h3>
    <p>프로젝트 초기에 경계를 잡아두면 나중에 observability와 환경별 설정 분기가 덜 아프다.</p>
  </div>
</div>

## Code Review Lens

- route가 transport adapter처럼 얇고, service가 business action을 대표하는지 본다.
- settings/env lookup이 service boundary 바깥의 wiring에서 정리되는지 본다.
- repository가 query/persistence detail만 알고 commit 정책은 모르는지 본다.
- 외부 side effect가 durable commit 뒤에 실행되는지 본다.

## Common Anti-Patterns

- route 안에서 env lookup, query, commit, publish, serialization을 모두 처리한다.
- repository/helper가 암묵적으로 commit해서 transaction 원자성이 깨진다.
- ORM entity를 request/response schema처럼 직접 사용한다.
- observability, timeout, retry를 나중에 붙일 일로 미뤄 entrypoint가 비대해진다.

## Likely Discussion Questions

- 현재 구조에서 feature flag, audit log, outbox를 넣으려면 어디가 가장 먼저 깨지는가?
- 왜 repository가 아니라 service/use case가 commit을 소유해야 하는가?
- background task나 worker가 같은 business action을 재사용하려면 어떤 경계를 유지해야 하는가?
- settings를 직접 읽는 코드가 늘어날수록 테스트와 운영에서 무슨 비용이 생기는가?

## Strong Answer Frame

- 먼저 boundary별 책임을 정리해 route, service, repository, infra의 역할을 구분한다.
- 현재 구조가 만드는 partial commit, 테스트 과대화, 운영 가시성 부족을 설명한다.
- 가장 작은 구조 개선으로 settings 주입, service orchestration, DTO 경계를 복원한다.
- 마지막에 retry/idempotency/observability 같은 운영 요구를 어디에 붙일지 연결한다.

## 함께 보면 좋은 예제

- `examples/fastapi_service_template_example.py`
- `examples/sqlalchemy_loading_strategies.py`
- `examples/sqlalchemy_class_based_uow.py`
- `tests/test_fastapi_fixtures_and_teardown.py`

## 리팩터링 동선

- 공통 냄새를 빠르게 찾고 싶다면 [Refactoring Atlas](/playbooks/refactoring-atlas)를 먼저 본다.
- route와 dependency 경계를 실제로 고치는 흐름은 [Refactoring Fat Routes and Dependency Leakage](/playbooks/refactoring-fat-routes-and-dependency-leakage)에서 이어진다.

## 공식 자료

- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
