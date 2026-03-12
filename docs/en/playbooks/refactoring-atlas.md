# Refactoring Atlas

<p class="lead">This page is a quick lookup atlas for recurring service-code smells. The goal is not to finish every refactor here, but to make it obvious what failure mode a smell leads to and what the first safe move should be.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: architecture-first refactoring is mostly about restoring ownership, not launching a giant redesign. Put routes back in charge of transport, dependencies back in charge of wiring, services and use cases back in charge of business actions, repositories back in charge of persistence detail, and DTOs back in charge of external contracts.</p>
</div>

## Atlas at a glance

| smell | first safe move | go deeper next |
| --- | --- | --- |
| fat route | remove business branching and commit ownership from the route first | [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage) |
| dependency leakage | make dependencies do resource wiring only again | [Dependency Injection](/en/fastapi/dependency-injection) |
| hidden commit | remove `commit()` from repositories/helpers and move it to the service/use-case boundary | [Refactoring Session Ownership and Hidden Commits](/en/playbooks/refactoring-session-ownership-and-hidden-commits) |
| split session ownership | unify who opens and closes the session | [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work) |
| DTO/ORM boundary collapse | split request DTOs, response DTOs, and ORM entities again | [Refactoring DTO Boundaries and Over-Abstraction](/en/playbooks/refactoring-dto-boundaries-and-over-abstraction) |
| env/settings lookup in service code | push `os.getenv()` and secret lookups back to wiring and settings providers | [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings) |
| over-abstracted ABCs or generic repositories | remove abstractions that provide no substitution value | [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc) |
| import-time side effects in app wiring | move initialization into app factory, lifespan, or explicit bootstrap functions | [API Service Template](/en/playbooks/api-service-template) |

## 1) Fat Route

- `typical symptom`: the route handles validation, auth, queries, commits, serialization, and feature flags itself.
- `why it hurts`: HTTP tests absorb business-rule verification and the right home for tracing, timeouts, or retries becomes unclear.
- `first safe refactor move`: move business branching and commit ownership into a service or use case first.
- `what not to do`: try to decompose every route in the codebase in one sweep.
- `where to go deeper next`: [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage), [Project Structure](/en/fastapi/project-structure)

## 2) Dependency Injection Leakage

- `typical symptom`: a dependency reads feature flags, branches on permissions, commits, or calls external APIs.
- `why it hurts`: DI stops being framework wiring and becomes a hidden business layer that is expensive to override and reuse.
- `first safe refactor move`: let dependencies assemble sessions, settings, principals, and clients only, and move branching back into services.
- `what not to do`: treat cleanup-heavy resources and simple object construction as the same kind of dependency.
- `where to go deeper next`: [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage), [Dependency Injection](/en/fastapi/dependency-injection)

## 3) Hidden Commit Inside a Repository or Helper

- `typical symptom`: `save()` or helper methods call `commit()` internally.
- `why it hurts`: partial commits appear inside what should have been one business action, and rollback reasoning gets muddy.
- `first safe refactor move`: let repositories stage or query only, and move commit ownership back to the service or use case boundary.
- `what not to do`: spread commits around as a temporary convenience and call it pragmatic.
- `where to go deeper next`: [Refactoring Session Ownership and Hidden Commits](/en/playbooks/refactoring-session-ownership-and-hidden-commits), [Session and Unit of Work](/en/sqlalchemy/session-and-unit-of-work)

## 4) Split Session Ownership

- `typical symptom`: the request dependency opens one live session while a helper or UoW opens another one for the same action.
- `why it hurts`: code looks like one use case but actually runs across multiple transaction scopes, which makes stale state and rollback logic harder to reason about.
- `first safe refactor move`: pick one owner for opening and closing the session per request, use case, or job.
- `what not to do`: mix live sessions, session factories, and UoWs in one flow without a single ownership story.
- `where to go deeper next`: [Refactoring Session Ownership and Hidden Commits](/en/playbooks/refactoring-session-ownership-and-hidden-commits), [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)

## 5) DTO / ORM Boundary Collapse

- `typical symptom`: request schemas, response schemas, and ORM entities are effectively treated as one type.
- `why it hurts`: persistence changes disturb public API contracts and lazy loading starts leaking into serialization.
- `first safe refactor move`: split request DTOs, response DTOs, and ORM entities into at least three explicit types.
- `what not to do`: justify the collapse with `from_attributes=True` alone.
- `where to go deeper next`: [Refactoring DTO Boundaries and Over-Abstraction](/en/playbooks/refactoring-dto-boundaries-and-over-abstraction), [FastAPI + Pydantic + SQLAlchemy](/en/playbooks/fastapi-pydantic-sqlalchemy)

## 6) Env / Settings Lookup Inside Service Code

- `typical symptom`: `os.getenv()`, `.env` assumptions, or secret lookups appear throughout service methods.
- `why it hurts`: tests cannot replace configuration cleanly and environment differences leak straight into business branching.
- `first safe refactor move`: inject a settings object from wiring and let services receive already-interpreted configuration.
- `what not to do`: wrap env lookup in tiny helpers and leave it callable from everywhere.
- `where to go deeper next`: [API Service Template](/en/playbooks/api-service-template), [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings)

## 7) Over-Abstracted ABCs or Generic Repositories

- `typical symptom`: repositories, services, DTOs, and mappers all hide behind ABCs or generic interfaces.
- `why it hurts`: query shape and transaction ownership disappear behind abstractions that provide little real substitution value.
- `first safe refactor move`: remove abstractions that do not improve substitution or testing.
- `what not to do`: abstract every layer just because the codebase wants to sound SOLID.
- `where to go deeper next`: [Refactoring DTO Boundaries and Over-Abstraction](/en/playbooks/refactoring-dto-boundaries-and-over-abstraction), [Use Case + UoW + ABC](/en/playbooks/usecase-uow-and-abc)

## 8) Import-Time Side Effects in App Wiring

- `typical symptom`: importing a module already opens DB clients, initializes SDKs, or performs app wiring.
- `why it hurts`: tests become hard to isolate and startup/shutdown behavior becomes opaque.
- `first safe refactor move`: move initialization into app factories, lifespan handlers, or explicit bootstrap functions.
- `what not to do`: rely on import order tricks instead of removing the side effect.
- `where to go deeper next`: [API Service Template](/en/playbooks/api-service-template), [Project Structure](/en/fastapi/project-structure)

## Suggested reading flow

1. Start here if you want a fast map of recurring smells.
2. Go to [Refactoring Fat Routes and Dependency Leakage](/en/playbooks/refactoring-fat-routes-and-dependency-leakage) if the route and DI boundary is the main problem.
3. Go to [Refactoring Session Ownership and Hidden Commits](/en/playbooks/refactoring-session-ownership-and-hidden-commits) if transaction and session ownership are the main problem.
4. Go to [Refactoring DTO Boundaries and Over-Abstraction](/en/playbooks/refactoring-dto-boundaries-and-over-abstraction) if DTO/ORM/ABC boundaries are blurred.
