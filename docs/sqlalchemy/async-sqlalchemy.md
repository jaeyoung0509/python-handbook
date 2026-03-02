# Async SQLAlchemy

<p class="lead">`AsyncSession`을 붙였다고 설계가 자동으로 좋아지지는 않는다. 오히려 async 환경에서는 "한 세션을 여러 task가 동시에 공유하면 안 된다", "lazy load가 숨어서 발생하면 안 된다" 같은 규칙이 더 엄격해진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: async SQLAlchemy는 "세션 하나를 request 또는 task 하나에만 묶고", "명시적 eager loading으로 숨은 I/O를 제거하고", "write transaction은 `async with session.begin()`으로 끝낸다"가 핵심이다.</p>
</div>

## async에서 특히 조심할 구조

<MermaidDiagram
  caption="AsyncSession은 event loop 안에서 I/O를 await하는 작업 문맥이다. 동시에 여러 task가 한 세션을 같이 건드리면 안 된다."
  chart="flowchart LR; A[FastAPI Request] --> B[AsyncSession Dependency]; B --> C[Service Use Case]; C --> D[async with session.begin()]; D --> E[(Database)]; C --> F[Explicit eager loading]; F --> G[Response DTO];"
/>

## 기본 설정

```py
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = "postgresql+asyncpg://app:secret@localhost/app"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session
```

<p class="code-caption">`expire_on_commit=False`는 async 환경에서 commit 이후 속성 접근이 추가 I/O를 유발하는 상황을 줄이기 위해 자주 권장된다. SQLAlchemy 공식 asyncio 문서도 이 설정을 대표 예제로 제시한다.</p>

## write path는 이렇게 잡는 편이 좋다

```py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_customer(self, customer_id: int) -> CustomerModel | None:
        return await self.session.get(CustomerModel, customer_id)

    def add(self, order: OrderModel) -> None:
        self.session.add(order)


class CreateOrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orders = OrderRepository(session)

    async def execute(self, customer_id: int, total: int) -> OrderRead:
        async with self.session.begin():
            customer = await self.orders.get_customer(customer_id)
            if customer is None:
                raise CustomerNotFound(customer_id)

            order = OrderModel(customer_id=customer.id, total=total)
            self.orders.add(order)
            await self.session.flush()

            return OrderRead(
                id=order.id,
                customer_id=order.customer_id,
                total=order.total,
            )
```

## read path는 숨은 lazy load를 피해야 한다

```py
from sqlalchemy import select
from sqlalchemy.orm import selectinload

stmt = (
    select(OrderModel)
    .options(selectinload(OrderModel.lines))
    .where(OrderModel.id == order_id)
)

row = await session.scalar(stmt)
if row is None:
    raise OrderNotFound(order_id)

return OrderDetail(
    id=row.id,
    total=row.total,
    lines=[
        OrderLineRead(product_id=line.product_id, quantity=line.quantity)
        for line in row.lines
    ],
)
```

<p class="code-caption">응답 직렬화 시점에 ORM 관계를 건드리면 lazy load가 터지기 쉽다. async에서는 이런 "숨은 I/O"가 특히 위험하므로, `selectinload()`나 `joinedload()` 같은 명시적 로딩 전략을 먼저 잡는 편이 안전하다.</p>

## 절대 공유하면 안 되는 것

- 같은 `AsyncSession`을 `asyncio.gather()`나 `TaskGroup`의 여러 task에서 동시에 쓰는 것
- 요청이 끝난 뒤 background task가 request session을 계속 들고 있는 것
- response serialization 과정에서 세션이 이미 닫힌 뒤 lazy load를 기대하는 것

## 동시 task가 필요하면 세션도 나눠야 한다

```py
import asyncio
from sqlalchemy import select


async def fetch_user_name(factory: async_sessionmaker[AsyncSession], user_id: int) -> str | None:
    async with factory() as session:
        stmt = select(UserModel.name).where(UserModel.id == user_id)
        return await session.scalar(stmt)


async def fetch_pair(factory: async_sessionmaker[AsyncSession]) -> tuple[str | None, str | None]:
    async with asyncio.TaskGroup() as tg:
        first = tg.create_task(fetch_user_name(factory, 1))
        second = tg.create_task(fetch_user_name(factory, 2))

    return first.result(), second.result()
```

## async SQLAlchemy 설계 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>세션은 task-local</h3>
    <p>한 세션을 여러 coroutine이 동시에 공유하지 않는다. concurrent work면 세션도 분리한다.</p>
  </div>
  <div class="check-card">
    <h3>implicit I/O 금지</h3>
    <p>응답 직렬화, property 접근, relationship traversal 시 lazy load가 숨어 나오지 않게 한다.</p>
  </div>
  <div class="check-card">
    <h3>write는 begin 블록</h3>
    <p>명시적 transaction context를 써서 commit/rollback 위치를 고정한다.</p>
  </div>
  <div class="check-card">
    <h3>sync bridge는 임시 수단</h3>
    <p>기존 sync 코드를 `run_sync()`로 감싸는 방식은 마이그레이션에는 유용하지만 기본 설계로 남기지 않는 편이 좋다.</p>
  </div>
</div>

## 공식 자료

- [SQLAlchemy AsyncIO Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Preventing Implicit IO when Using AsyncSession](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession)
