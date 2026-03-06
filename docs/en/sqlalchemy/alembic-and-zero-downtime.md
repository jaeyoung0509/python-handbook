# Alembic and Zero-Downtime Migrations

<p class="lead">Even if a team uses SQLAlchemy well, weak migration discipline will still break production. The core idea behind Alembic is not "my models changed, so generate some SQL". The real job is to manage deployable schema change units as a revision graph. In live systems that usually means separating expand, dual write, backfill, cutover, and contract.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: Alembic is not a model-snapshot button. It manages schema history. Autogenerate is only a starting point, and zero-downtime migrations come from additive changes plus staged rollout between the application and the database.</p>
</div>

<MermaidDiagram
  caption="Real migration work is usually staged rollout, not one DDL statement."
  chart="flowchart LR; A[&quot;expand schema&quot;] --> B[&quot;deploy app with dual read or dual write&quot;]; B --> C[&quot;backfill old rows&quot;]; C --> D[&quot;switch reads and writes&quot;]; D --> E[&quot;contract old column or constraint&quot;];"
/>

## 1) What Alembic should mean to you

Alembic is not a "sync the DB to my current model state" button.

A better mental model is:

- a revision is one deployable schema change unit
- revisions form a graph
- a production database has a current revision state
- application versions and schema versions do not always move in lockstep

That makes migration an operational object, not just part of the app code.

## 2) You need the revision graph, not only the latest head

A basic Alembic revision points to its previous node via `down_revision`.

```py
revision = "20260306_add_display_name"
down_revision = "20260215_initial_users"
branch_labels = None
depends_on = None
```

The key point is not merely "keep one latest head". You also need to understand why merge revisions exist once multiple branches introduce migrations at the same time.

### When branches appear

- one feature branch adds an index
- another feature branch adds a column
- both land on main and now the revision graph has two heads

If that branch state is ignored, different environments can drift in migration order and state.

## 3) Autogenerate is a drafting assistant, not an approval step

Autogenerate helps with:

- adding tables and columns
- spotting many simple metadata differences
- producing a first draft of upgrade/downgrade code

Autogenerate does not solve:

- data-migration strategy
- long backfill planning
- lock-impact analysis
- destructive change rollout
- intent around renames versus drop-and-add sequences

So `alembic revision --autogenerate` is a starting point, not the final answer.

Renames are one of the most common traps.

- Alembic usually cannot infer that "this is only a rename" from metadata diff alone.
- a change like `full_name -> display_name` can show up as `drop_column + add_column`
- in production that difference is critical, because a real rename needs expand, dual read, backfill, and contract thinking rather than blindly executing the draft

## 4) Why naming conventions matter first

If the database invents constraint names for you, diffs and rollback work become harder to read.

```py
from sqlalchemy import MetaData


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
```

Stable naming makes Alembic diffs calmer and operational tracing easier.

## 5) The zero-downtime baseline: expand -> migrate data -> contract

Suppose you want to replace `full_name` with `display_name`.

### Fragile approach

1. drop the old column
2. add the new column
3. deploy the new application at the same time

This breaks as soon as one combination of old app, new app, old schema, and new schema overlaps.

### Safer approach

1. add the new column as nullable: `expand`
2. deploy the app with dual read or dual write behavior
3. backfill old rows
4. switch reads and writes to the new column
5. remove the old column last: `contract`

## 6) Always build the compatibility table

| App version | Schema state | Safe? | Why |
| --- | --- | --- | --- |
| old app | old schema | yes | original pairing |
| old app | expanded schema | yes | additive changes are often compatible |
| new app | expanded schema | yes | dual read/write preserves compatibility |
| new app | contracted schema | yes | safe after cutover |
| old app | contracted schema | no | old code may still expect removed columns |

That is why contract phases belong last.

## 7) Data migration is not the same kind of work as schema migration

An `ALTER TABLE` and a backfill touching millions of rows do not have the same operational profile.

### Why to treat data migration separately

- it takes longer
- it can hold locks longer
- it may increase WAL, replication lag, or storage churn
- it often needs batching, restartability, and progress visibility

Many teams embed heavy backfills directly inside one migration revision. That can be much riskier than using a separate batch job or operational worker step.

Lock behavior also depends heavily on the actual database engine.

- PostgreSQL may rewrite a table or take strong locks for some `ALTER TABLE` operations. Even index creation may need a special path such as `CONCURRENTLY`.
- MySQL or InnoDB online DDL behavior varies by version and operation. "online" does not automatically mean "no user-visible impact".
- SQLite often rebuilds tables for schema changes, which makes it convenient for local development but a weak proxy for production zero-downtime behavior.

Migration risk has to be assessed against the real production engine, not only the ORM layer.

## 8) Why not to auto-run migrations during app startup

It may feel convenient in development, but production costs are high.

- multiple workers may race to run the same migration
- startup latency becomes unpredictable
- app health and schema state fail together
- Lambda cold starts are a terrible place to hide schema migration work

Recommended rule:

- run migrations as a CI/CD or operational job
- let the app start assuming the schema is already correct

## 9) Alembic operations checklist

### Before writing a revision

- can the change be split into additive phases?
- is this really a rename, or a destructive drop plus add?
- are constraint and index names stable?
- is a backfill required?

### During review

- did you review the autogenerate output instead of trusting it blindly?
- was destructive work split into rollout phases?
- is downgrade truly realistic, or is app rollback / forward fix the real plan?
- did you consider long-lock risk?

### Before deployment

- is old app plus new schema safe?
- can new app plus old schema appear even briefly?
- does this interact badly with readiness, draining, or worker restarts?

Operational rollback is also not the same thing as a template `downgrade()` function.

- after destructive migrations, you may not be able to reconstruct the original data exactly
- once a backfill has enforced new invariants, rolling back only the schema may not restore the previous state
- in practice, rollback often depends more on app rollback, feature flags, or forward fixes than on returning to an older Alembic revision

## 10) Alembic quality follows SQLAlchemy modeling quality

- unstable naming leads to unstable diffs
- mixing domain renames with DB renames makes rollout harder
- clear session and UoW boundaries make dual write placement easier

Migration discipline is an extension of modeling discipline.

## 11) The hardest part is CI/CD and progressive delivery

Real services need more than clean revision files.

- migration jobs should be separated from app deploy jobs
- larger backfills are safer as resumable operational jobs
- rolling, blue-green, and canary still cannot avoid schema compatibility rules when the DB is shared

That operational layer is covered in more depth in [Progressive Delivery + Alembic](/en/playbooks/progressive-delivery-and-alembic), and the broader DB/API/event/backfill view continues in [Contract Evolution and Sustainable CD](/en/playbooks/contract-evolution-and-sustainable-cd).

## Good companion chapters in this repository

1. [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
2. [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)
3. [Lambda vs Kubernetes](/en/playbooks/lambda-vs-kubernetes)
4. [Progressive Delivery + Alembic](/en/playbooks/progressive-delivery-and-alembic)
5. [Contract Evolution and Sustainable CD](/en/playbooks/contract-evolution-and-sustainable-cd)

For runnable intuition, see `examples/alembic_zero_downtime_lab.py` and `examples/progressive_delivery_backfill_lab.py`.

## Official References

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- [SQLAlchemy naming conventions](https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions)
