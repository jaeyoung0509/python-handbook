# Core vs ORM

<p class="lead">To understand SQLAlchemy 2.0 properly, it helps to stop thinking of Core and ORM as competing modes. ORM queries are built on top of Core statements, and real applications usually need both: Core for SQL shape and projection control, ORM for identity, mapping, and unit-of-work behavior.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: Core is closer to SQL expression construction and execution. ORM is closer to mapped objects and change tracking. They are different layers, not mutually exclusive choices. Reporting, aggregation, and bulk operations often benefit from Core-first thinking; write-heavy aggregate logic often benefits from ORM.</p>
</div>

## The Big Picture

<MermaidDiagram
  caption="In SQLAlchemy 2.0, ORM work still leans heavily on statement construction. Core sits below as the SQL layer; ORM adds mapping, identity, and unit-of-work behavior on top."
  chart="flowchart TB; A[Table metadata and SQL expressions] --> B[Core statement objects]; B --> C[Engine and Connection execution]; B --> D[ORM Session execution]; D --> E[Mapped entities and identity map];"
/>

## Where Core Excels

- complex joins, CTEs, and window functions
- bulk inserts, updates, and deletes
- reporting and dashboard queries
- projection queries that do not need entity hydration

## Where ORM Excels

- entity creation and change tracking
- relationships and aggregates
- flush and commit coordination
- write paths that need rich object lifecycles

## The 2.0 Style Shift

In ORM code too, it is better to think in terms of `select()` statements than old-style `Query` chains.

```py
from sqlalchemy import select
from sqlalchemy.orm import Session


def list_active_users(session: Session) -> list[User]:
    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.created_at.desc())
    )
    return list(session.scalars(stmt))
```

<p class="code-caption">This returns ORM entities, but the query itself is a Core-style statement. That statement-first mindset is central to reading and writing SQLAlchemy 2.0 code.</p>

## A Projection Query with Core Flavor

```py
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def count_users_by_role(session: Session) -> list[tuple[str, int]]:
    stmt = (
        select(User.role, func.count(User.id))
        .group_by(User.role)
        .order_by(User.role)
    )
    return [(role, count) for role, count in session.execute(stmt)]
```

- No mapped entity is necessary here.
- Reporting endpoints often fit projection queries better than entity graphs.
- Read models and write models do not need to have the same shape.

## When to Lean More Toward Core

| Situation | Better default | Why |
| --- | --- | --- |
| domain write path | ORM-centric | state tracking and unit-of-work behavior fit naturally |
| dashboards and reports | Core projections | entity hydration may add no value |
| large bulk changes | Core or bulk strategy | avoids per-entity tracking cost |
| SQL-heavy optimization | Core-centric | gives more direct SQL shape control |

## Bad Ways to Mix Them

- forcing every query result into mapped entities
- forcing every code path into tuple rows and losing ORM value
- combining write models, read models, and ad-hoc analytics into one repository abstraction

## Design Guidance

- Use ORM where aggregate state and transaction ownership matter.
- Use projection-oriented statements where API shape matters more than object identity.
- Even Core-style statements can run through the session, so transaction ownership still lives at the use-case boundary.

## Practical Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Separate read and write shapes</h3>
    <p>Do not force entity-heavy abstractions onto reporting or list endpoints that only need projections.</p>
  </div>
  <div class="check-card">
    <h3>Think statement first</h3>
    <p>`select()` plus loader options is the natural reading model for SQLAlchemy 2.0.</p>
  </div>
  <div class="check-card">
    <h3>Notice hydration cost</h3>
    <p>Mapped entities are useful, but not free. Use them when identity and state tracking actually matter.</p>
  </div>
  <div class="check-card">
    <h3>Keep session ownership intact</h3>
    <p>Core-style querying does not remove the need for coherent transaction ownership.</p>
  </div>
</div>

## Official References

- [SQLAlchemy Unified Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [SQLAlchemy ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
- [SQLAlchemy Core Tutorial](https://docs.sqlalchemy.org/en/20/core/tutorial.html)
