# Progressive Delivery + Alembic

<p class="lead">Rolling updates, blue-green, and canary deployments shift application traffic gradually. They do not split your production database into safe isolated copies. In most services, the database remains one shared singleton, which means old and new application versions must coexist against the same schema for some period of time. In that situation, Alembic is not merely a DDL runner. It is part of the compatibility contract between rollout phases.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: in shared-database systems, the main deployment question is not only "how do we shift traffic?" but "how long can old and new app versions tolerate the same schema?". The safest default is `expand migration -> compatibility app deploy -> resumable backfill -> progressive traffic shift -> feature flag cutover -> later contract migration`.</p>
</div>

<MermaidDiagram
  caption="Whether the rollout is rolling, blue-green, canary, or Lambda alias-based, shared-schema compatibility is still the common backbone."
  chart="flowchart LR; A[&quot;CI: revision review and upgrade test&quot;] --> B[&quot;CD: expand migration job&quot;]; B --> C[&quot;deploy compatibility version&quot;]; C --> D[&quot;run resumable backfill&quot;]; D --> E[&quot;progressive traffic shift&quot;]; E --> F[&quot;feature flag cutover&quot;]; F --> G[&quot;later contract migration&quot;];"
/>

## 1) First truth to accept: the database is usually shared

Blue-green or canary may give you multiple application versions, but most production systems still have one primary database schema.

That makes these questions central:

- is old app plus expanded schema safe?
- is new app plus expanded schema safe?
- from which point does old app plus contracted schema become impossible?

Traffic strategy and schema compatibility are different concerns.

## 2) How to use Alembic in CI

A common mistake is to stop after verifying that a revision file exists. In practice CI should go further.

### Baseline CI checks

1. review `alembic revision --autogenerate` output manually
2. verify `alembic upgrade head` on an ephemeral database
3. ideally replay upgrade from the current production head to the candidate head
4. run application tests against the upgraded schema
5. confirm whether the change is destructive, requires backfill, or needs rollout splitting

### Questions CI should answer

- is this really a rename, or did it become drop plus add?
- did autogenerate miss index or constraint intent?
- is a contract step hidden inside the same release?
- is the data migration small enough for an Alembic revision, or does it need a separate job?

## 3) Default CD shape: separate migration jobs from deploy jobs

The safest baseline looks like this.

### Step 1. expand migration job

- add nullable columns
- add additive indexes, tables, or constraints
- apply only changes that do not break the old application

### Step 2. compatibility app deploy

- deploy a version that understands both old and new schema shapes
- prepare `dual read`, `dual write`, or flags with the feature still off
- do not contract yet

### Step 3. backfill job

- run larger data migrations as a separate job or worker
- include chunked transactions, checkpoints, retry, and metrics

### Step 4. progressive traffic shift

- use rolling update, blue-green, canary, or Lambda alias traffic shifting
- schema still needs to be tolerated by both old and new versions

### Step 5. cutover

- switch reads or writes to the new column via feature flag or config
- watch metrics, error rate, and lag

### Step 6. later contract migration

- remove old columns or constraints only after the old app is fully gone
- usually in a later release after stabilization

## 4) A good GitHub Actions gate layout

For shared-database systems, it is often a mistake to run database changes and app deployment as one unprotected job.

Splitting GitHub Actions environments lets you separate approval and protection for DB and app changes.

```yaml
name: deploy

on:
  push:
    branches: [main]

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run pytest
      - run: uv run ruff check .
      - run: uv run ty check

  migrate-expand:
    needs: test-and-build
    runs-on: ubuntu-latest
    environment: production-db
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run alembic upgrade head

  deploy-compatible:
    needs: migrate-expand
    runs-on: ubuntu-latest
    environment: production-app
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy-compatible.sh

  backfill:
    needs: deploy-compatible
    runs-on: ubuntu-latest
    environment: production-db
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run python -m app.jobs.backfill_display_name --batch-size 1000

  promote-traffic:
    needs: backfill
    runs-on: ubuntu-latest
    environment: production-app
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/promote-traffic.sh
```

<p class="code-caption">The important idea is separating `production-db` from `production-app`. Database approvals, app approvals, and backfill timing are often different concerns.</p>

## 5) When backfill belongs inside Alembic and when it does not

| Case | Inside Alembic revision | Separate backfill job |
| --- | --- | --- |
| small data fix that completes in seconds | yes | optional |
| long-running update with batching and resume needs | no | yes |
| lock-sensitive change that needs throttling | no | yes |
| production migration that needs live metrics watching | no | yes |

The distinction is between a small schema-adjacent data fix and a real operational migration job.

## 6) Properties of a good backfill job

### 1. Idempotent

Reprocessing already-filled rows should be safe.

```sql
UPDATE users
SET display_name = full_name
WHERE display_name IS NULL
  AND id BETWEEN :start_id AND :end_id
```

### 2. Resumable

- keep a checkpoint table or external cursor
- store fields such as `last_processed_id`, `updated_rows`, and `updated_at`

### 3. Bounded transactions

- do not update millions of rows in one transaction
- commit every small batch

### 4. Observable

- rows per second
- lag
- remaining null count
- error count
- last cursor

### 5. Throttled

- batch size or pause intervals should be adjustable from operational signals such as DB CPU, lock pressure, or replica lag

## 7) A Python backfill worker baseline

```py
def run_backfill(session_factory: SessionFactory, batch_size: int = 1000) -> None:
    cursor = load_checkpoint("users_display_name")

    while True:
        with session_factory() as session:
            rows = session.execute(
                select(User.id, User.full_name)
                .where(User.id > cursor, User.display_name.is_(None))
                .order_by(User.id)
                .limit(batch_size)
            ).all()

            if not rows:
                return

            for user_id, full_name in rows:
                session.execute(
                    update(User)
                    .where(User.id == user_id, User.display_name.is_(None))
                    .values(display_name=full_name)
                )

            cursor = rows[-1][0]
            save_checkpoint(session, "users_display_name", cursor)
            session.commit()
```

This pattern shows keyset cursoring, small transactions, and checkpoint persistence together.

## 8) Rules for rolling updates

Kubernetes `Deployment` rolling updates keep old and new ReplicaSets alive together for a while.

That leads to a simple rule set:

- run expand migrations first
- the new app must support dual read or dual write if needed
- contract only after old pods are fully gone

Rolling updates are operationally simple, but they make N-1 and N compatibility requirements the most obvious.

## 9) Rules for blue-green

Blue-green gives you a preview stack, which is excellent for validation, but it does not give you automatic database isolation.

### Safe sequence

1. expand migration
2. deploy green
3. run preview smoke or analysis
4. run backfill if needed
5. switch traffic
6. keep blue alive while post-promotion checks run
7. remove blue after stabilization
8. contract later

### Core misunderstanding to avoid

Blue-green does not automatically create a `blue DB` and `green DB`. If the DB is shared, schema still must stay backward compatible.

## 10) Rules for canary

Canary reduces blast radius for application behavior, but it does not make destructive schema changes safe.

### Why

- even 1% canary traffic still reads and writes the shared DB
- stable 99% and canary 1% still touch the same tables and rows
- destructive schema work remains dangerous

### What canary is good for

- application behavior analysis
- query cost, latency, and error-rate analysis
- validating feature flags before full promotion

### What canary is not good for

- contract migrations that old code cannot tolerate
- lock-heavy rewrites
- "it's only 1%, so destructive DDL is fine" reasoning

## 11) Lambda weighted alias and CodeDeploy canary follow the same DB rule

AWS Lambda weighted aliases and CodeDeploy canary or linear strategies shift application traffic, not schema compatibility requirements.

Additional Lambda-specific points:

- an alias can point to at most two versions
- at low traffic, actual traffic split can vary meaningfully from the configured percentage
- weighted alias is useful for canarying app code, not for avoiding proper expand/backfill/contract sequencing

So the order is still the same: `expand -> compatible code -> backfill -> traffic shift -> contract later`.

## 12) Strategy comparison table

| Strategy | Strength | Key schema rule | Common mistake |
| --- | --- | --- | --- |
| rolling update | simplest operationally | old and new pods must coexist safely | putting contract in the same release |
| blue-green | strong preview validation | shared DB still requires backward compatibility | contracting immediately after promotion |
| canary | controlled blast radius, metrics-driven promotion | schema does not become safe just because traffic is small | assuming 1% makes destructive migration safe |
| Lambda alias / CodeDeploy | serverless gradual traffic shift | same DB compatibility rule still applies | mixing weighted routing with destructive DB change |

## 13) Common mistakes to avoid

- auto-running Alembic during app startup
- putting a huge backfill inside one Alembic revision transaction
- assuming blue-green reduces schema compatibility work
- assuming low canary percentage makes destructive migration acceptable
- running contract immediately after traffic promotion

## Good companion chapters in this repository

1. [Alembic and Zero-Downtime Migrations](/en/sqlalchemy/alembic-and-zero-downtime)
2. [Lambda vs Kubernetes](/en/playbooks/lambda-vs-kubernetes)
3. [Contract Evolution and Sustainable CD](/en/playbooks/contract-evolution-and-sustainable-cd)
4. [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)

For runnable intuition, pair this with `examples/progressive_delivery_backfill_lab.py`.

## Official References

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [Deployments | Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Argo Rollouts Canary](https://argo-rollouts.readthedocs.io/en/stable/features/canary/)
- [Argo Rollouts BlueGreen](https://argo-rollouts.readthedocs.io/en/latest/features/bluegreen/)
- [AWS Lambda weighted alias routing](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)
