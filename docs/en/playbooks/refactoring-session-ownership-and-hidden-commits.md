# Refactoring Session Ownership and Hidden Commits

<p class="lead">Session ownership and hidden commits are among the most common structural sources of SQLAlchemy bugs. Code may look like "one business action," but if repositories, helpers, and dependencies each own their own session or commit behavior, rollback reasoning and incident analysis become much harder.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: fix ownership first. Decide who opens and closes the session, decide who finalizes the transaction, and let repositories keep only persistence detail. That is the safest foundation for later UoW patterns.</p>
</div>

## 1) sub-optimal snippet

```py
from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker


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

## 2) What is the exact smell?

- The repository performs a hidden commit.
- The audit repository opens a second session for what looks like the same business action.
- The route sees one service call, but the transaction boundary has already split in two.

That makes partial success easy: the order may commit while audit fails, or audit may survive while the order rolls back elsewhere.

## 3) The smallest safe refactor sequence

1. Remove `commit()` from repositories and helpers.
2. Make repositories that participate in one business action share one session.
3. Move commit ownership to the service or use-case boundary.
4. Only after that, introduce a class-based UoW if repository grouping still needs clearer ownership.

The key is that you do not need a UoW first. You need clear ownership first.

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

At that point, if repository groups grow and you want the transaction boundary to read as one explicit object, you can move from direct session injection to a class-based UoW. But removing hidden commits and restoring single-owner session lifecycle still comes first.

## 5) What gets better

- `tests`: fake repositories or fake UoWs can verify "one use case, one commit" far more clearly.
- `operations`: partial commits, connection leaks, and stale-state bugs become easier to reason about.
- `change isolation`: audit logging, outbox writes, or extra repositories can join the same action without fragmenting ownership.

## Code Review Lens

- Check whether one boundary clearly opens and closes the session.
- Check whether commit happens once per business action.
- Check whether repositories or helpers avoid hidden commits and surprise session creation.
- Check whether `flush()` and `commit()` remain mentally separate.

## Common Anti-Patterns

- repositories calling `commit()` inside `save()`
- helper functions quietly opening their own sessions
- request dependencies injecting one live session while a UoW opens another one internally
- compensating for broken ownership with more exception handling instead of fixing the boundary

## Likely Discussion Questions

- Why is repository commit more than a small convenience?
- When is direct session injection clearer, and when is a class-based UoW clearer?
- Why can `flush()` be useful while `commit()` must stay explicit?
- What should you remove first when hidden commits already exist?

## Strong Answer Frame

- Start by exposing how many transaction boundaries the current code really creates.
- Explain how hidden commits and split session ownership create partial-success failure modes.
- Move repositories back to pure persistence detail and move commit ownership to the service or use case.
- Close by framing UoW as a later readability tool, not the first rescue move.

## Good companion chapters

- [Refactoring Atlas](/en/playbooks/refactoring-atlas)
- [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
- [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)
- [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)
