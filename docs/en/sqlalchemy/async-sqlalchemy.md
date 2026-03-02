# Async SQLAlchemy

<p class="lead">Adding `AsyncSession` does not magically fix design problems. In async code, the rules get stricter: you must not share one session across concurrent tasks, and hidden lazy-load I/O becomes even more dangerous.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: async SQLAlchemy works best when each request or task owns its own `AsyncSession`, write paths use `async with session.begin()`, and read paths eagerly load everything the response will need.</p>
</div>

## The Async Shape to Aim For

<MermaidDiagram
  caption="An AsyncSession is an awaitable work context inside the event loop. It should be local to one request or one task, not shared across concurrent tasks."
  chart="flowchart LR; A[FastAPI Request] --> B[AsyncSession Dependency]; B --> C[Service Use Case]; C --> D[async with session.begin()]; D --> E[(Database)]; C --> F[Explicit eager loading]; F --> G[Response DTO];"
/>

## Baseline Configuration

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

<p class="code-caption">`expire_on_commit=False` is commonly recommended for async usage because it reduces surprise I/O after commit. SQLAlchemy's asyncio documentation uses that pattern in its examples.</p>

## A Good Write Path

```py
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

## Read Paths Must Prevent Hidden I/O

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

<p class="code-caption">In async code, it is especially important that response serialization does not trigger lazy loading. Load relationships explicitly before you build the response DTO.</p>

## Never Share These

- One `AsyncSession` across several `asyncio.gather()` or `TaskGroup` tasks
- A request-scoped session inside background work that outlives the request
- ORM entities that still rely on lazy loading after the session is closed

## If Work Is Concurrent, Sessions Must Be Separate Too

```py
import asyncio
from sqlalchemy import select


async def fetch_user_name(
    factory: async_sessionmaker[AsyncSession],
    user_id: int,
) -> str | None:
    async with factory() as session:
        stmt = select(UserModel.name).where(UserModel.id == user_id)
        return await session.scalar(stmt)


async def fetch_pair(factory: async_sessionmaker[AsyncSession]) -> tuple[str | None, str | None]:
    async with asyncio.TaskGroup() as tg:
        first = tg.create_task(fetch_user_name(factory, 1))
        second = tg.create_task(fetch_user_name(factory, 2))

    return first.result(), second.result()
```

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Session is task-local</h3>
    <p>Do not let multiple coroutines mutate the same AsyncSession concurrently.</p>
  </div>
  <div class="check-card">
    <h3>No implicit I/O</h3>
    <p>Prevent lazy loading during serialization or property access.</p>
  </div>
  <div class="check-card">
    <h3>Writes use explicit transaction blocks</h3>
    <p>Keep commit and rollback locations obvious.</p>
  </div>
  <div class="check-card">
    <h3>Sync bridges are temporary</h3>
    <p>`run_sync()` can help during migrations, but should not become your default architecture.</p>
  </div>
</div>

## Official Sources

- [SQLAlchemy AsyncIO Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Preventing Implicit IO when Using AsyncSession](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession)
