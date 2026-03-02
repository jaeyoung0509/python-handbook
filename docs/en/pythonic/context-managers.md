# Context Managers

## Why It Matters

`with` is Python's standard way to express scoped resource ownership, cleanup, and transactional boundaries.

## This Chapter Builds

- what the `with` statement actually does
- `__enter__` and `__exit__`
- `contextlib`
- async context managers
- transaction, lifespan, and resource-scope patterns

## Practical Connections

- database session scope
- FastAPI lifespan wiring
- test fixtures and cleanup behavior
