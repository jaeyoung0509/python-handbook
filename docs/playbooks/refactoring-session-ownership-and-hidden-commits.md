# Refactoring Session Ownership and Hidden Commits

<p class="lead">session ownership과 hidden commit 문제는 SQLAlchemy 서비스에서 가장 흔한 구조적 버그 원인이다. 겉으로는 "한 번의 business action"처럼 보이는데 실제로는 repository, helper, dependency가 제각각 세션과 commit을 소유하면 rollback reasoning과 장애 분석이 급격히 어려워진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 가장 먼저 고쳐야 할 것은 session을 누가 열고 닫는지, commit을 누가 확정하는지다. repository는 저장/조회 detail만 남기고, service나 use case가 하나의 transaction boundary를 소유하도록 되돌리는 것이 가장 안전하다.</p>
</div>

## 1) sub-optimal snippet

```py
from fastapi import Depends
from sqlalchemy.orm import Session


def get_order_service(session: Session = Depends(get_session)) -> "OrderService":
    return OrderService(session)


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, order: OrderRecord) -> None:
        self.session.add(order)
        self.session.commit()


class AuditRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def record(self, event: AuditEvent) -> None:
        with self.session_factory() as session:
            session.add(AuditRecord.from_event(event))
            session.commit()


class OrderService:
    def __init__(self, session: Session) -> None:
        self.orders = OrderRepository(session)
        self.audit = AuditRepository(SessionFactory)

    def create_order(self, command: CreateOrderCommand) -> OrderRead:
        record = OrderRecord(customer_id=command.customer_id, total=command.total)
        self.orders.add(record)
        self.audit.record(AuditEvent("order.created", record.id))
        return OrderRead(id=record.id, total=record.total)
```

## 2) 정확한 냄새는 무엇인가

- repository가 hidden commit을 수행한다.
- 같은 business action 안에서 audit repository가 별도 session을 또 연다.
- route는 한 service call만 보지만 실제로는 transaction boundary가 둘이다.

이 구조에서는 "주문 생성은 성공했는데 audit는 실패했다" 또는 반대로 "audit는 남았는데 주문은 rollback됐다" 같은 partial success가 쉽게 생긴다.

## 3) 가장 작은 안전한 리팩터링 순서

1. repository에서 `commit()`을 제거하고 `add()`/query만 남긴다.
2. 같은 business action 안에서 사용하는 repository는 같은 session을 공유하게 만든다.
3. service/use case가 commit을 한 번만 수행하게 만든다.
4. repository 수가 많아 ownership이 흐려지면 그때 class-based UoW로 올린다.

중요한 점은 바로 UoW를 도입하는 것보다 먼저 hidden commit을 없애고 ownership을 한 곳으로 모으는 것이다.

## 4) improved end state

```py
from sqlalchemy.orm import Session


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, order: OrderRecord) -> None:
        self.session.add(order)


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, event: AuditEvent) -> None:
        self.session.add(AuditRecord.from_event(event))


class OrderService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.orders = OrderRepository(session)
        self.audit = AuditRepository(session)

    def create_order(self, command: CreateOrderCommand) -> OrderRead:
        with self.session.begin():
            record = OrderRecord(customer_id=command.customer_id, total=command.total)
            self.orders.add(record)
            self.session.flush()
            self.audit.record(AuditEvent("order.created", record.id))
            return OrderRead(id=record.id, total=record.total)
```

이 시점부터 repository 수가 늘고 transaction 묶음을 더 명시적으로 표현하고 싶다면 `session` 직접 주입 대신 UoW factory 패턴으로 옮길 수 있다. 하지만 hidden commit 제거와 single-owner session 복구가 항상 먼저다.

## 5) 무엇이 좋아지나

- `tests`: fake repository나 fake UoW로 "한 use case, 한 commit"을 더 명확히 검증할 수 있다.
- `operations`: partial commit, connection leak, stale state 원인을 더 쉽게 추적할 수 있다.
- `change isolation`: audit, outbox, additional repository가 붙어도 transaction reasoning이 유지된다.

## Code Review Lens

- 누가 session을 열고 닫는지 한 경계로 읽히는지 본다.
- commit이 business action 단위에서 한 번만 일어나는지 본다.
- repository/helper가 hidden commit이나 별도 session opening을 하지 않는지 본다.
- `flush()`와 `commit()`의 역할이 구분돼 있는지 본다.

## Common Anti-Patterns

- repository `save()`가 내부적으로 `commit()`을 호출한다.
- helper 함수가 조용히 새 session을 열고 닫는다.
- request dependency가 live session을 주입하는데 UoW도 또 내부 session을 만든다.
- session ownership 문제를 덮기 위해 예외 처리만 더 두껍게 만든다.

## Likely Discussion Questions

- 왜 repository commit은 작은 편의가 아니라 큰 구조적 비용이 되는가?
- direct session injection과 class-based UoW 중 무엇을 언제 고르는가?
- `flush()`는 필요하지만 `commit()`은 숨기면 안 되는 이유가 무엇인가?
- hidden commit 구조에서 가장 먼저 끊어야 할 연결은 무엇인가?

## Strong Answer Frame

- 먼저 현재 구조가 실제로 몇 개의 transaction boundary를 만드는지 드러낸다.
- 다음으로 hidden commit과 split session ownership이 partial success를 어떻게 만드는지 설명한다.
- repository는 persistence detail만 남기고 commit ownership을 service/use case로 올린다.
- 마지막으로 필요 시 UoW는 ownership을 더 읽기 좋게 만드는 다음 단계라고 정리한다.

## 같이 읽으면 좋은 문서

- [Refactoring Atlas](/playbooks/refactoring-atlas)
- [Session and Unit of Work](/sqlalchemy/session-and-unit-of-work)
- [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)
- [Deployment and Engine Settings](/sqlalchemy/deployment-and-engine-settings)
