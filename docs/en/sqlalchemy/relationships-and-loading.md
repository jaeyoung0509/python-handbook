# Relationships and Loading

<p class="lead">A large share of SQLAlchemy performance issues comes not from the relationship declaration itself, but from when and how related data is loaded. Hidden lazy loads create N+1 behavior, while overusing joined eager loading can produce row explosion and heavy result sets.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: loading strategy is part of query design, not a secondary ORM option. Start with the API response shape you need, then choose loader options intentionally at query time.</p>
</div>

## Loading Strategy Overview

<MermaidDiagram
  caption="Relationship loading changes both SQL count and row shape. It is a query-design decision, not just a convenience feature."
  chart="flowchart LR; A[Select parent rows] --> B{Loader strategy}; B --> C[lazy: extra query on access]; B --> D[joinedload: join in same query]; B --> E[selectinload: secondary IN query]; B --> F[subqueryload: secondary subquery];"
/>

## The Main Strategies

| Strategy | Strength | Risk | Good fit |
| --- | --- | --- | --- |
| `lazy` | simple default | N+1 and hidden I/O | internal code paths that rarely touch the relationship |
| `joinedload()` | one query with related rows | duplicated parent rows, wide joins | detail views, small related sets |
| `selectinload()` | stable collection loading | still uses secondary queries | list APIs with moderate collections |
| `subqueryload()` | useful in some shapes | often more complex than `selectinload()` | special or legacy cases |

## A Common List-API Pattern

```py
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


def list_orders(session: Session) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(50)
    )
    return list(session.scalars(stmt))
```

<p class="code-caption">For one-to-many collections in list endpoints, `selectinload()` is often the most balanced starting point. It avoids row explosion while still fetching the related collection predictably.</p>

## Detail Views Often Fit `joinedload()`

```py
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload


def get_order_detail(session: Session, order_id: int) -> Order | None:
    stmt = (
        select(Order)
        .options(joinedload(Order.customer))
        .where(Order.id == order_id)
    )
    return session.scalar(stmt)
```

- This is often natural for many-to-one or small related objects.
- It is a poor default for large one-to-many collections because row duplication can grow quickly.

## API Design and Loading Strategy Should Be Coupled

- Decide the response DTO shape first.
- Attach loader options in the query layer to match that shape.
- Do not let serializers discover missing relationships later by triggering lazy loads.
- In async code, hidden lazy loading is even more problematic.

## `lazy="raise"` Can Surface Design Errors Early

```py
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    items: Mapped[list["OrderItem"]] = relationship(lazy="raise")
```

If the relationship was not preloaded, `lazy="raise"` makes access fail fast instead of silently issuing SQL. This is especially useful near serialization boundaries.

## Cascades Are Domain Rules, Not Just Convenience

- Use `delete-orphan` only when parent ownership is truly strong.
- Cascade configuration should reflect aggregate boundaries.
- Overly broad cascade settings can create surprising deletes.

## Common Mistakes

- leaving list endpoints on default lazy loading
- enabling eager loading on every relationship globally
- not knowing what the serializer touches
- enabling cascades without a clear ownership model

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Start from response shape</h3>
    <p>Choose loader options based on what the API actually needs to return.</p>
  </div>
  <div class="check-card">
    <h3>Try `selectinload()` for collections first</h3>
    <p>For one-to-many list responses, it is often the most stable first choice.</p>
  </div>
  <div class="check-card">
    <h3>Use `joinedload()` for small detail graphs</h3>
    <p>It works well when row explosion risk is limited and one round trip is valuable.</p>
  </div>
  <div class="check-card">
    <h3>Fail fast on hidden lazy loads</h3>
    <p>Use tools like `lazy="raise"` to catch accidental SQL at serialization time.</p>
  </div>
</div>

## Official References

- [SQLAlchemy Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [SQLAlchemy Basic Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
