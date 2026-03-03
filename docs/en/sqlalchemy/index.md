# SQLAlchemy 2.0

<p class="lead">Using SQLAlchemy well is less about memorizing ORM syntax and more about separating `Session`, transaction ownership, loading strategy, and API boundaries. In web services, most complexity comes from getting those boundaries wrong.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: treat `Session` as a unit-of-work and transaction boundary, not as a cache or a global DB handle. Repositories talk to the session, but commits belong at the use-case boundary.</p>
</div>

## The Questions That Matter Most

<div class="reading-grid">
  <div class="reading-card">
    <h3>What is a Session?</h3>
    <p>It is a short-lived work context that combines identity mapping and unit-of-work behavior.</p>
  </div>
  <div class="reading-card">
    <h3>Who owns commit?</h3>
    <p>The use case or service layer should own transaction completion, not the repository.</p>
  </div>
  <div class="reading-card">
    <h3>Can ORM entities cross the API boundary?</h3>
    <p>Usually they should not. Lazy loading, serialization, and schema evolution become tightly coupled.</p>
  </div>
  <div class="reading-card">
    <h3>When is async worth it?</h3>
    <p>When your whole stack is async and high-concurrency I/O matters. Session-sharing rules become stricter, not looser.</p>
  </div>
  <div class="reading-card">
    <h3>How should settings change by deployment target?</h3>
    <p>Lambda, Kubernetes, workers, and batch jobs do not share the same process lifetime or connection budget. Copy-pasting one pool configuration is a fast way to overload the database.</p>
  </div>
</div>

## Recommended Reading Order

1. [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)
2. [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)
3. [Relationships and Loading](/en/sqlalchemy/relationships-and-loading)
4. [Async SQLAlchemy](/en/sqlalchemy/async-sqlalchemy)
5. [Core vs ORM](/en/sqlalchemy/core-vs-orm)
6. [Migrations and Patterns](/en/sqlalchemy/migrations-and-patterns)

## Working Rules for Real Services

- Keep sessions scoped to a request or use case.
- Do not `commit()` inside repositories.
- Match engine and pool settings to the deployment process model.
- Design read and write paths differently.
- Do not collapse ORM entities, Pydantic schemas, and domain concepts into one class.
- In async code, never share an `AsyncSession` across concurrent tasks.

## Good Companion Chapters

- [Project Structure](/en/fastapi/project-structure)
- [Dependency Injection](/en/fastapi/dependency-injection)
- [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)
