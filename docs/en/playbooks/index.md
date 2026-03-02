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
    <h3>Where does theory meet service design?</h3>
    <p>It connects typing, runtime, and framework knowledge to concrete API architecture decisions.</p>
  </div>
</div>

## Recommended Reading Order

1. [API Service Template](/en/playbooks/api-service-template)
2. [Testing with Fixtures](/en/playbooks/testing-with-pytest-fixtures)
3. [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
4. [Typing Review Checklist](/en/playbooks/typing-review-checklist)

## How to Use This Part

- Start with `API Service Template` when creating a new service skeleton.
- Start with `Testing with Fixtures` if you need a clean fixture and teardown baseline for service tests.
- Start with `FastAPI + Pydantic + SQLAlchemy` if you already have a service and want cleaner boundaries.
- Use `Typing Review Checklist` as a team review baseline.

## Good Companion Chapters

- [FastAPI](/en/fastapi/)
- [Pydantic](/en/pydantic/)
- [SQLAlchemy 2.0](/en/sqlalchemy/)
- [Typing](/en/typing/)
