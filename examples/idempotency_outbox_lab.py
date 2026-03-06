from __future__ import annotations

# What this lab adds / 이 예제가 추가하는 것:
# - Show class-based UoW with idempotency and outbox repositories.
# - class 기반 UoW와 idempotency/outbox 저장소를 함께 보여준다.
# - Show how same-key retries are deduped and conflicting payloads are rejected.
# - 같은 key 재시도는 dedupe되고 다른 payload는 거부되는 흐름을 보여준다.
#
# Why it was added / 왜 추가되었나:
# - Retry-safe write paths are a core production concern, not an edge case.
# - retry-safe write path는 엣지 케이스가 아니라 실서비스 핵심 관심사다.
# - Outbox only becomes clear when seen next to the transaction boundary.
# - outbox는 transaction 경계 옆에서 봐야 역할이 선명해진다.
#
# When to use this / 언제 보면 좋은가:
# - When designing POST/create APIs under retry and duplicate-delivery pressure.
# - retry와 duplicate-delivery 압력이 있는 POST/create API를 설계할 때.
# - When deciding whether `BackgroundTasks` is enough for event publication.
# - event publish에 `BackgroundTasks`로 충분한지 판단할 때.
import abc
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast
from uuid import uuid4


def payload_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class CreateOrderCommand:
    idempotency_key: str
    customer_id: str
    amount: int

    def fingerprint(self) -> str:
        return payload_fingerprint(
            {"customer_id": self.customer_id, "amount": self.amount}
        )


@dataclass(frozen=True, slots=True)
class OrderPlacedEvent:
    order_id: str
    customer_id: str
    amount: int


@dataclass(slots=True)
class Order:
    id: str
    customer_id: str
    amount: int
    _pending_events: list[OrderPlacedEvent] = field(default_factory=list)

    @classmethod
    def create(cls, command: CreateOrderCommand) -> "Order":
        order = cls(
            id=str(uuid4()),
            customer_id=command.customer_id,
            amount=command.amount,
        )
        order._pending_events.append(
            OrderPlacedEvent(
                order_id=order.id,
                customer_id=order.customer_id,
                amount=order.amount,
            )
        )
        return order

    def pull_events(self) -> list[OrderPlacedEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    topic: str
    payload: dict[str, Any]

    @classmethod
    def from_event(cls, event: OrderPlacedEvent) -> "OutboxMessage":
        return cls(
            topic="order.placed",
            payload={
                "order_id": event.order_id,
                "customer_id": event.customer_id,
                "amount": event.amount,
            },
        )


@dataclass(frozen=True, slots=True)
class StoredResponse:
    fingerprint: str
    body: dict[str, Any]


class OrdersRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, order: Order) -> None:
        raise NotImplementedError


class IdempotencyRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str) -> StoredResponse | None:
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, key: str, response: StoredResponse) -> None:
        raise NotImplementedError


class OutboxRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, message: OutboxMessage) -> None:
        raise NotImplementedError


class UnitOfWork(abc.ABC):
    orders: OrdersRepository
    idempotency: IdempotencyRepository
    outbox: OutboxRepository

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError


class InMemoryOrdersRepository(OrdersRepository):
    def __init__(self) -> None:
        self.items: list[Order] = []

    def add(self, order: Order) -> None:
        self.items.append(order)


class InMemoryIdempotencyRepository(IdempotencyRepository):
    def __init__(self) -> None:
        self.items: dict[str, StoredResponse] = {}

    def get(self, key: str) -> StoredResponse | None:
        return self.items.get(key)

    def save(self, key: str, response: StoredResponse) -> None:
        self.items[key] = response


class InMemoryOutboxRepository(OutboxRepository):
    def __init__(self) -> None:
        self.items: list[OutboxMessage] = []

    def add(self, message: OutboxMessage) -> None:
        self.items.append(message)


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.orders = InMemoryOrdersRepository()
        self.idempotency = InMemoryIdempotencyRepository()
        self.outbox = InMemoryOutboxRepository()
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class CreateOrderUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateOrderCommand) -> dict[str, Any]:
        fingerprint = command.fingerprint()
        existing = self._uow.idempotency.get(command.idempotency_key)
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise ValueError("same idempotency key reused with different payload")
            return existing.body

        order = Order.create(command)
        self._uow.orders.add(order)

        for event in order.pull_events():
            self._uow.outbox.add(OutboxMessage.from_event(event))

        response = {"order_id": order.id, "status": "created"}
        self._uow.idempotency.save(
            command.idempotency_key,
            StoredResponse(fingerprint=fingerprint, body=response),
        )
        self._uow.commit()
        return response


def main() -> None:
    uow = InMemoryUnitOfWork()
    use_case = CreateOrderUseCase(uow)
    orders_repo = cast(InMemoryOrdersRepository, uow.orders)
    outbox_repo = cast(InMemoryOutboxRepository, uow.outbox)

    first_command = CreateOrderCommand(
        idempotency_key="order-001",
        customer_id="neo",
        amount=100,
    )
    same_retry = CreateOrderCommand(
        idempotency_key="order-001",
        customer_id="neo",
        amount=100,
    )
    conflicting_retry = CreateOrderCommand(
        idempotency_key="order-001",
        customer_id="neo",
        amount=999,
    )

    first_response = use_case.execute(first_command)
    second_response = use_case.execute(same_retry)

    print("== idempotent create ==")
    print(first_response)
    print(second_response)
    print(f"orders stored: {len(orders_repo.items)}")
    print(f"outbox messages stored: {len(outbox_repo.items)}")
    print(f"commits: {uow.commits}")

    print("\n== conflicting retry ==")
    try:
        use_case.execute(conflicting_retry)
    except ValueError as error:
        print(error)


if __name__ == "__main__":
    main()
