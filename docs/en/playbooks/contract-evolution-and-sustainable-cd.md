# Contract Evolution and Sustainable CD

<p class="lead">In systems with frequent schema change, the hard problem is not a handful of Alembic commands. The production database schema, the public API, the async event contract, and the historical data each evolve at different speeds. When teams blur those boundaries, they over-version APIs, keep risky dual-write paths too long, and place backfills in the wrong layer. This page lays out how to evolve contracts without turning continuous delivery into synchronized big-bang releases.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: sustainable CD means avoiding a world where every participant must upgrade at the same moment. The safe baseline is `additive DB expand -> compatibility app deploy -> additive API or event adapter / version bridge -> resumable backfill or replay -> feature-flag cutover -> later contract removal`.</p>
</div>

<MermaidDiagram
  caption="Sustainable delivery starts by treating DB schema, API contract, and event contract as different compatibility problems rather than one giant migration task."
  chart="flowchart LR; A[&quot;clients v1 and v2&quot;] --> B[&quot;API boundary adapter&quot;]; B --> C[&quot;core service&quot;]; C --> D[&quot;expanded DB schema&quot;]; C --> E[&quot;outbox&quot;]; E --> F[&quot;event bridge or v2 event&quot;]; D --> G[&quot;backfill or rebuild&quot;]; F --> H[&quot;old and new consumers&quot;]; G --> I[&quot;cutover and later contract&quot;];"
/>

## 1) Start by separating three contracts

| Contract | Main consumers | Example break | Default mitigation |
| --- | --- | --- | --- |
| DB schema | old/new app versions, batch jobs, admin scripts | column drop, rename, tighter constraint | expand/contract, dual read/write, backfill |
| Sync API contract | mobile apps, external customers, frontend | field removal, meaning change, new required field | additive change first, boundary adapter, API version if needed |
| Async event contract | consumer services, data pipelines, webhook receivers | semantic event change, new required field, ordering-key change | additive event, upcaster/downcaster, new event type or v2 |

If teams treat those as one problem, they usually make one of these mistakes:

- a DB column rename becomes an unnecessary public API version bump
- an event schema change gets treated like a normal DTO refactor
- a historical-data problem is handled as if an application deploy alone can solve it

The compatibility audience and observation window are different for each contract.

## 2) Questions to ask before versioning

Before introducing a new version, ask these first:

1. can the change stay additive?
2. can an old client or old consumer still be alive for a while?
3. does historical data need to be reshaped?
4. is the meaning changing, or only the representation?

The central rule is simple:

- if the meaning is stable and only the representation changes, adapters and additive change are often enough
- if the meaning changes, a new version or new event type is much more likely to be justified

## 3) A fast decision table

| Situation | DB strategy | API strategy | Event strategy | Data work |
| --- | --- | --- | --- | --- |
| internal column rename (`full_name -> display_name`) | expand -> dual read/write -> contract | usually no version | often none | backfill |
| add a new optional public response field | additive column or projection | add field without version | additive field if needed | usually none |
| remove or semantically change a public field | split DB work from API change | deprecate, then version or keep a transition field | if related meaning changes, consider a new event type | maybe backfill |
| add an optional event field | additive schema only if needed | unrelated | existing event can often stay | usually none |
| change event meaning (`order.created` no longer means the same thing) | separate DB concern | separate API concern | new event type or `v2` | maybe replay or bridging |
| change a derived read model shape | preserve source of truth | adapter or projection switch | keep event log stable | rebuild or replay may fit better than backfill |

So "change happened, therefore add a new version" is not a strong default.

## 4) DB schema evolution: Alembic starts the job, rollout discipline finishes it

As covered in [Alembic and Zero-Downtime Migrations](/en/sqlalchemy/alembic-and-zero-downtime) and [Progressive Delivery + Alembic](/en/playbooks/progressive-delivery-and-alembic), the baseline for shared-database systems is `expand -> backfill -> contract`.

It helps to separate the strategies explicitly.

| Strategy | When to use it | Why | Cost |
| --- | --- | --- | --- |
| expand/contract | old and new app versions coexist | delay destructive change until old code is gone | more releases |
| dual read | old and new representations coexist in storage | preserve read compatibility before cutover | temporary read complexity |
| dual write | both old and new shapes must be populated | separate cutover timing from historical repair | drift prevention is required |
| separate backfill job | large data volume, resume/retry needed | separate DDL from operational migration work | needs workers, metrics, checkpoints |
| lazy backfill | only hot rows need to converge over time | reduce the cost of a full historical sweep | convergence takes longer |
| rebuild/replay | derived projections or read models | recreating from source of truth is safer | replay time and infra cost |

One distinction matters a lot:

- dual-writing old and new columns inside one database transaction can be practical
- dual-writing to the database and a broker as separate best-effort actions is risky; that is usually an outbox problem instead

## 5) API versioning: version the boundary, not the core

The healthiest default is often "version-aware at the boundary, versionless in the core".

That means:

- routes or serializers understand `v1` vs `v2`
- the service or use-case layer tries to keep one stable domain model
- request and response translation happens at the edges instead of forking business logic everywhere

It also helps to keep public and internal boundaries separate in your head.

- public APIs need real deprecation windows because you usually cannot control consumer upgrade timing
- internal service calls, admin APIs, or module boundaries inside one codebase do not all deserve public-style versioning
- for internal boundaries, additive DTO changes, deployment ordering, adapters, and feature flags are often cheaper than version tags everywhere

### When API versioning is justified

- external clients live a long time
- the change is clearly breaking, such as field removal or meaning change
- you cannot control upgrade timing for consumers

### When not to rush into a new version

- adding an optional field
- adding a new endpoint
- adding additive response data
- a rename that can keep the old representation temporarily

### How to choose a scheme

| Scheme | Best fit | Strength | Weakness |
| --- | --- | --- | --- |
| path version (`/v1/...`) | public APIs where docs and gateway separation matter | very explicit and operationally simple | URL shape becomes part of the version contract |
| header version | stable URL is important for the same resource | clean URLs | testing and docs are slightly harder |
| query version | transition period or legacy gateway | easy to introduce | noisier URLs and weaker consistency |
| date-based version | SaaS or public APIs with long deprecation policy | change timing stays explicit | version semantics must stay disciplined |

The deeper rule matters more than the scheme: once versioning leaks into `v1_service`, `v2_service`, and duplicated business rules, maintenance cost rises fast.

Deprecation windows should match the kind of consumer you actually have.

- tightly controlled internal consumers can often tolerate short windows and hard cutovers
- mobile apps, partner integrations, and public APIs usually need longer windows
- before announcing removal dates, you need logs, metrics, or access reports that show who still depends on the old contract

## 6) Event versioning: the contract that hurts longest

Events are asynchronous, consumers can reconnect late, and historical replay may matter. That makes event contracts more conservative than synchronous APIs.

### When additive event evolution is enough

- you only add an optional field
- old consumers can ignore unknown fields
- the event meaning and ordering key stay the same

### When a new event type or `v2` is safer

- the event name stays the same but the meaning changes
- a new required field would break old consumers
- the partition key, ordering, or idempotency identity changes
- the business semantics changed, not only the payload structure

### Practical strategies

| Strategy | When to use it | Strength | Watch out |
| --- | --- | --- | --- |
| additive field | tolerant readers are possible | lowest operational cost | needs consumer contract tests |
| upcaster/downcaster | keep the topic stable with a translation layer | smoother producer/consumer transition | translation layers become long-lived debt if not removed |
| new event type | semantics actually changed | makes the break explicit | two flows coexist for a while |
| dual publish | short-lived migration bridge | easy consumer transition | should stay temporary and is safest with outbox support |

If you use Kafka, Avro, or Protobuf with a schema registry, choose compatibility mode deliberately. `BACKWARD`, `FORWARD`, and `FULL_TRANSITIVE` are not cosmetic settings. They directly affect which side can be deployed first.

### How rollout order changes for producers and consumers

When a schema registry is involved, it helps to translate compatibility mode into rollout order.

- `BACKWARD` modes are about whether a new consumer can read data written with an older schema. In that setup, older consumers are not guaranteed to read data written with the new schema, so consumer upgrades usually come first.
- `FORWARD` modes are about whether older consumers can read data written with the new schema. That often supports producer-first rollout, provided you also account for historical data still in the topic.
- `FULL` modes give both directions of compatibility, which makes producer and consumer rollout more independent. They still do not make semantic changes safe by magic.

Registry compatibility is mostly about payload decoding. It does not replace review of business meaning, ordering rules, or consumer logic.

## 7) Backfill, replay, and rebuild are different jobs

Mixing these together is a common source of delivery pain.

- backfill: update historical source-of-truth rows to satisfy a new schema or invariant
- replay: reread an event log to regenerate derived state
- rebuild: recreate a projection, cache, search index, or other derived system from scratch

### Choosing the right one

| Problem | More natural choice |
| --- | --- |
| fill a new nullable column with historical values | backfill |
| replace a read-model schema | rebuild or replay |
| only active rows need to converge over time | lazy backfill |
| resend historical external payloads under a new contract | evaluate a replay or republisher pipeline |

Good backfill or rebuild jobs usually share the same properties:

- idempotent
- resumable
- bounded transactions or bounded batches
- progress metrics
- validation queries

Useful validation signals include:

- `new_column IS NULL` row count
- old/new representation mismatch count
- consumer lag or projection lag
- replay cursor or checkpoint

## 8) The baseline sequence for sustainable CD

1. classify the change into DB, API, event, and data concerns
2. decide whether additive DB expand is possible
3. add an API adapter or event bridge so old and new consumers can coexist
4. deploy the compatibility version
5. run backfill, replay, or rebuild as separate operational work
6. cut over through feature flags, routing, or config
7. watch metrics and mismatch counts until stable
8. remove the old contract later

The critical distinction is between `cutover` and `contract`.

- cutover means the new path becomes the default
- contract means the old path is physically removed

Putting both in the same release makes rollback much harder.

Before removing the old contract, it is worth confirming at least these signals:

- old API-version traffic or old event-consumer traffic has effectively fallen to zero during the deprecation window
- backfill mismatch counts and `NULL` counts are within the agreed threshold
- the feature flag or routing rollback path still exists
- external consumers such as partners or mobile clients were actually notified of the removal schedule

## 9) Common mistakes to avoid

- bumping the public API version the moment you notice a DB rename
- pretending an event semantic change is just a minor payload tweak
- running dual publish as if it were a permanent design
- forcing a huge backfill through one Alembic revision
- contracting while old consumers are still alive
- assuming versioning reduces the need for observability and deprecation policy

## 10) Team checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Is this a real semantic break?</h3>
    <p>Separate representation change from consumer-meaning change before choosing a strategy.</p>
  </div>
  <div class="check-card">
    <h3>Can this stay additive?</h3>
    <p>New versions are usually cheaper as a last resort than as a default reflex.</p>
  </div>
  <div class="check-card">
    <h3>Is only the boundary version-aware?</h3>
    <p>Do not let the entire service core split into version branches unless there is no alternative.</p>
  </div>
  <div class="check-card">
    <h3>Does this require backfill or replay?</h3>
    <p>If code deploy alone cannot repair historical state, schedule explicit operational work.</p>
  </div>
  <div class="check-card">
    <h3>Is contract removal the last step?</h3>
    <p>Keep an observation window after cutover before physically deleting the old path.</p>
  </div>
</div>

## Good companion chapters

1. [Alembic and Zero-Downtime Migrations](/en/sqlalchemy/alembic-and-zero-downtime)
2. [Progressive Delivery + Alembic](/en/playbooks/progressive-delivery-and-alembic)
3. [Idempotency and Outbox](/en/playbooks/idempotency-and-outbox)
4. [Client Protocol and Reconnect](/en/fastapi/websocket-client-protocol-and-reconnect)

## Official References

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [SQLAlchemy naming conventions](https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions)
- [Confluent Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)
- [Stripe API versioning](https://docs.stripe.com/api/versioning)
- [Stripe webhook versioning](https://docs.stripe.com/webhooks/versioning)
- [Versions in Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/api-management-versions)
