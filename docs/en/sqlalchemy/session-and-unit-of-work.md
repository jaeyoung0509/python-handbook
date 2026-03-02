# Session and Unit of Work

## Why It Matters

Many SQLAlchemy bugs start with a wrong mental model of `Session`. It is not just a connection holder or cache.

## This Chapter Builds

- session lifecycle
- transaction boundaries
- `flush` vs `commit`
- identity map behavior
- request-scoped session patterns
