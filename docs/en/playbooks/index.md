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
    <h3>Where should a refactor start?</h3>
    <p>It connects recurring smells such as fat routes, hidden commits, and DTO/ORM collapse to one atlas plus focused refactoring series.</p>
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

1. [Refactoring Atlas](/en/playbooks/refactoring-atlas)
2. [API Service Template](/en/playbooks/api-service-template)
3. [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage)
4. [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings)
5. [ABC + Fake UoW Testing](/en/playbooks/testing-abc-and-fake-uow)
6. [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)
7. [Refactoring Session Ownership and Hidden Commits](/en/playbooks/refactoring-session-ownership-and-hidden-commits)
8. [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
9. [Refactoring DTO Boundaries and Over-Abstraction](/en/playbooks/refactoring-dto-boundaries-and-over-abstraction)
10. [Testing with Fixtures](/en/playbooks/testing-with-pytest-fixtures)
11. [Testing Beyond Fixtures](/en/playbooks/testing-beyond-fixtures)
12. [Lambda vs Kubernetes](/en/playbooks/lambda-vs-kubernetes)
13. [Progressive Delivery + Alembic](/en/playbooks/progressive-delivery-and-alembic)
14. [Contract Evolution and Sustainable CD](/en/playbooks/contract-evolution-and-sustainable-cd)
15. [Idempotency and Outbox](/en/playbooks/idempotency-and-outbox)
16. [Typing Review Checklist](/en/playbooks/typing-review-checklist)

## How to Read This Part in Review Mode

- Key playbooks now end with `Code Review Lens`, `Common Anti-Patterns`, `Likely Discussion Questions`, and `Strong Answer Frame`.
- `API Service Template` and `Use Case + UoW + ABC` now include `sub-optimal -> improved` examples that show concrete refactoring direction.
- `Refactoring Atlas` works as a fast smell index, while the refactoring series pages teach each smell in a deeper narrative form.
- `Lambda vs Kubernetes` and `Progressive Delivery + Alembic` now include symptom-first scenario tables for operational judgment.

## How to Use This Part

- Start with `Refactoring Atlas` if you want to classify the smell before choosing a deeper chapter.
- Start with `Refactoring Fat Routes and Dependency Leakage` if route and DI boundaries are tangled.
- Start with `API Service Template` when creating a new service skeleton.
- Start with `Settings and Pydantic Settings` if you need a clean config boundary for env vars, secrets, and test overrides.
- Start with `Testing with Fixtures` if you need a clean fixture and teardown baseline for service tests.
- Start with `Testing Beyond Fixtures` if you want to add contract, property-based, and protocol testing on top of that baseline.
- Start with `ABC + Fake UoW Testing` if you want fast unit tests around use-case branching without touching a real database.
- Start with `Use Case + UoW + ABC` if you want a concrete SOLID-aware use-case boundary with SQLAlchemy and explicit abstract base classes.
- Start with `Refactoring Session Ownership and Hidden Commits` if hidden commits or split session ownership are the main smell.
- Start with `FastAPI + Pydantic + SQLAlchemy` if you already have a service and want cleaner boundaries.
- Start with `Refactoring DTO Boundaries and Over-Abstraction` if DTO/ORM collapse or low-value abstractions are the main problem.
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
