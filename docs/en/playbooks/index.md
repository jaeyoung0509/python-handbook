# Playbooks

<p class="lead">This section translates the earlier theory into practical service-design rules. Knowing Pythonic patterns, typing, runtime behavior, asyncio, FastAPI, Pydantic, and SQLAlchemy independently is useful, but what matters in production is how those pieces fit together without collapsing into one giant layer.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a playbook is not a summary page. It is a decision aid. You should be able to use these chapters when starting a service, reviewing code, or refactoring a codebase that has begun to tangle its boundaries.</p>
</div>

## The Questions This Part Answers

<div class="reading-grid">
  <div class="reading-card">
    <h3>How should a new service start?</h3>
    <p>It proposes a reference layout for routers, services, repositories, schemas, settings, logging, and tests.</p>
  </div>
  <div class="reading-card">
    <h3>How should configuration be designed?</h3>
    <p>It explains how to split `settings.py`, `pydantic-settings`, `.env`, secret sources, and test overrides into a clean configuration boundary.</p>
  </div>
  <div class="reading-card">
    <h3>How do FastAPI, Pydantic, and SQLAlchemy stay decoupled?</h3>
    <p>It separates request DTOs, transactions, ORM entities, and response DTOs so the API can evolve cleanly.</p>
  </div>
  <div class="reading-card">
    <h3>What should type reviews focus on?</h3>
    <p>It prioritizes `Any` containment, abstraction discipline, protocol usage, and boundary clarity over annotation volume.</p>
  </div>
  <div class="reading-card">
    <h3>How should fixture design work?</h3>
    <p>It covers yield fixtures, dependency override cleanup, database isolation, and client lifecycles as real service-testing patterns.</p>
  </div>
  <div class="reading-card">
    <h3>What comes after fixtures?</h3>
    <p>It explains how to add HTTP contract tests, websocket protocol tests, property-based tests, and idempotency invariants on top.</p>
  </div>
  <div class="reading-card">
    <h3>How do you choose Lambda vs Kubernetes?</h3>
    <p>It compares traffic shape, database connection strategy, long-lived connections, and operational surface area instead of treating hosting as an afterthought.</p>
  </div>
  <div class="reading-card">
    <h3>How do schema changes stay safe during progressive delivery?</h3>
    <p>It explains ordering for Alembic, backfill, and feature flags across rolling, blue-green, canary, and Lambda alias rollouts.</p>
  </div>
  <div class="reading-card">
    <h3>How do schema, API, and event contracts evolve together?</h3>
    <p>It brings DB migrations, API versioning, event versioning, and backfill or replay into one contract-evolution frame.</p>
  </div>
  <div class="reading-card">
    <h3>How do retries and duplicate delivery stay safe?</h3>
    <p>It connects idempotency keys, outbox design, publisher retry, and dedupe into one operational picture.</p>
  </div>
  <div class="reading-card">
    <h3>Where does theory meet service design?</h3>
    <p>It connects typing, runtime, and framework knowledge to concrete API architecture decisions.</p>
  </div>
</div>

## Recommended Reading Order

1. [API Service Template](/en/playbooks/api-service-template)
2. [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings)
3. [Testing with Fixtures](/en/playbooks/testing-with-pytest-fixtures)
4. [Testing Beyond Fixtures](/en/playbooks/testing-beyond-fixtures)
5. [ABC + Fake UoW Testing](/en/playbooks/testing-abc-and-fake-uow)
6. [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)
7. [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
8. [Lambda vs Kubernetes](/en/playbooks/lambda-vs-kubernetes)
9. [Progressive Delivery + Alembic](/en/playbooks/progressive-delivery-and-alembic)
10. [Contract Evolution and Sustainable CD](/en/playbooks/contract-evolution-and-sustainable-cd)
11. [Idempotency and Outbox](/en/playbooks/idempotency-and-outbox)
12. [Typing Review Checklist](/en/playbooks/typing-review-checklist)

## How to Read This Part in Review Mode

- Key playbooks now end with `Code Review Lens`, `Common Anti-Patterns`, `Likely Discussion Questions`, and `Strong Answer Frame`.
- `API Service Template` and `Use Case + UoW + ABC` now include `sub-optimal -> improved` examples that show concrete refactoring direction.
- `Lambda vs Kubernetes` and `Progressive Delivery + Alembic` now include symptom-first scenario tables for operational judgment.

## How to Use This Part

- Start with `API Service Template` when creating a new service skeleton.
- Start with `Settings and Pydantic Settings` if you need a clean config boundary for env vars, secrets, and test overrides.
- Start with `Testing with Fixtures` if you need a clean fixture and teardown baseline for service tests.
- Start with `Testing Beyond Fixtures` if you want to add contract, property-based, and protocol testing on top of that baseline.
- Start with `ABC + Fake UoW Testing` if you want fast unit tests around use-case branching without touching a real database.
- Start with `Use Case + UoW + ABC` if you want a concrete SOLID-aware use-case boundary with SQLAlchemy and explicit abstract base classes.
- Start with `FastAPI + Pydantic + SQLAlchemy` if you already have a service and want cleaner boundaries.
- Start with `Lambda vs Kubernetes` if the hosting decision is still open and you need a workload-driven rubric.
- Start with `Progressive Delivery + Alembic` if you need a safe order for schema changes, backfill jobs, and rollout promotion under rolling, blue-green, canary, or Lambda alias deployment.
- Start with `Contract Evolution and Sustainable CD` if you need one mental model for DB schema, public API, async events, and historical data migration.
- Start with `Idempotency and Outbox` if retry-safe create endpoints and reliable publication are becoming production concerns.
- Use `Typing Review Checklist` as a team review baseline.

## Good Companion Chapters

- [FastAPI](/en/fastapi/)
- [Pydantic](/en/pydantic/)
- [SQLAlchemy 2.0](/en/sqlalchemy/)
- [Typing](/en/typing/)
