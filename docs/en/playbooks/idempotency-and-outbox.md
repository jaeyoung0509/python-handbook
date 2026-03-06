# Idempotency and Outbox

<p class="lead">In real services, "this runs exactly once" is much less common than teams hope. Client retries, proxy retries, worker restarts, network timeouts, and duplicate event delivery all make duplicate execution normal. That is why create APIs and publish paths are safer when designed around idempotency keys and the transactional outbox pattern.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: idempotency makes repeated requests look like one logical action, while the outbox pattern makes database writes and future message publication part of one transaction boundary. Retry-heavy systems often need both together.</p>
</div>

<MermaidDiagram
  caption="If duplicate execution and message loss are not handled separately, API writes and async publication drift apart quickly."
  chart="flowchart LR; A[&quot;client request with idempotency key&quot;] --> B[&quot;use case&quot;]; B --> C[&quot;domain write&quot;]; C --> D[&quot;store idempotency record&quot;]; C --> E[&quot;store outbox message&quot;]; D --> F[&quot;commit&quot;]; E --> F; F --> G[&quot;outbox publisher&quot;];"
/>

## 1) Why idempotency matters

All of these are common:

- a client retries the same POST because of a timeout
- a reverse proxy or API gateway retries upstream
- the application succeeded but the response was lost
- a queue consumer receives the same event again under at-least-once delivery

Duplicate execution should therefore be treated as normal, not exceptional.

## 2) The baseline idempotency-key contract

A practical idempotency contract is usually:

- same key plus same payload: reuse the previous result
- same key plus different payload: reject with `409 Conflict` or similar
- store both a request fingerprint and a response snapshot

### Why that contract matters

If the system keys only on the idempotency key and ignores the payload, a reused key can accidentally return the wrong prior response.

## 3) What the key store should remember

At minimum, many systems need:

- idempotency key
- request fingerprint
- result snapshot
- status such as `in_progress`, `completed`, or `failed`
- TTL or retention policy

An `in_progress` state also helps handle concurrent duplicate requests more safely.

## 4) Why the outbox pattern exists

This sequence is risky:

1. write the order row
2. commit
3. publish `order.created`

If the process dies between steps 2 and 3, the database contains the order but the event never leaves. Reversing the order is also dangerous if publication succeeds but commit fails.

The outbox pattern stores both the domain write and the "message to publish later" inside the same DB transaction. A separate publisher then reads outbox rows and performs the actual broker publish.

## 5) Putting UoW and outbox together

```py
class UnitOfWork(abc.ABC):
    orders: OrdersRepository
    idempotency: IdempotencyRepository
    outbox: OutboxRepository

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError
```

```py
def handle(command: CreateOrderCommand, uow: UnitOfWork) -> dict[str, str]:
    existing = uow.idempotency.get(command.idempotency_key, command.payload_fingerprint)
    if existing is not None:
        return existing

    order = Order.create(...)
    uow.orders.add(order)
    uow.outbox.add(OutboxMessage.from_domain_event(order.pull_events()[0]))

    result = {"order_id": order.id, "status": "created"}
    uow.idempotency.save(command.idempotency_key, command.payload_fingerprint, result)
    uow.commit()
    return result
```

The key point is that the domain row, outbox row, and idempotency row stay inside the same transaction until commit.

## 6) Why `BackgroundTasks` is not enough

`BackgroundTasks` is in-process follow-up work.

- it can disappear if the process dies
- it has no built-in durability or retry semantics
- it is not atomic with the database write

That makes it a bad fit for must-deliver events or create flows that need durable exactly-once-like behavior at the API boundary.

## 7) Concurrency makes the design sharper

### API idempotency

- two requests with the same key can arrive at the same time
- a DB-level uniqueness strategy or `INSERT ... ON CONFLICT` style approach may be needed

### outbox publishing

- multiple publisher workers can race on the same outbox row
- status transitions, leasing, or `FOR UPDATE SKIP LOCKED` style coordination may be needed

So idempotency and outbox are not only conceptual patterns. They depend on storage atomicity and worker coordination.

## 8) A good starting path

### smaller service

- add idempotency keys to create endpoints
- keep one outbox table and one publisher worker
- mark failed publish attempts for retry

### larger service

- add outbox metadata such as `status`, `retry_count`, `next_attempt_at`, and `last_error`
- make dedupe keys and payload fingerprints explicit
- track metrics like duplicate hit rate, outbox lag, and retry rate

## 9) Common mistakes

- treating same key plus different payload as if it were the same logical request
- publishing events with a best-effort function call after commit
- having no dedupe strategy for at-least-once consumers
- adding an outbox but leaving publisher or consumer paths non-idempotent

## 10) Practical checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Do you store both the key and payload fingerprint?</h3>
    <p>You need to distinguish key reuse from the same logical request.</p>
  </div>
  <div class="check-card">
    <h3>Are domain write and outbox write in the same transaction?</h3>
    <p>If not, message loss or phantom events become possible.</p>
  </div>
  <div class="check-card">
    <h3>Do publish retry and dedupe exist?</h3>
    <p>Outbox alone does not remove duplicate-delivery concerns.</p>
  </div>
  <div class="check-card">
    <h3>Can you observe the pattern in production?</h3>
    <p>Duplicate hit rate and outbox lag should be visible metrics.</p>
  </div>
</div>

## Good companion chapters in this repository

1. [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)
2. [Background Tasks and Offloading](/en/fastapi/background-tasks-and-offloading)
3. [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
4. [Contract Evolution and Sustainable CD](/en/playbooks/contract-evolution-and-sustainable-cd)

For runnable code, see `examples/idempotency_outbox_lab.py`. For tests, see `tests/test_idempotency_and_contracts.py`.

## References

- [The Idempotency-Key HTTP Header Field](https://www.ietf.org/archive/id/draft-ietf-httpapi-idempotency-key-header-07.html)
- [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
