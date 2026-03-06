# Python Handbook

A practical Python 3.14 handbook built as a VitePress documentation site.

This repository is organized as a deep-dive study and reference project for:

- Pythonic design and the data model
- modern Python typing
- CPython runtime internals
- `asyncio`
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- service architecture playbooks

The documentation is available in both Korean and English, with runnable examples and tests alongside the handbook chapters.

## Live Site

- Korean: [https://jaeyoung0509.github.io/python-handbook/](https://jaeyoung0509.github.io/python-handbook/)
- English: [https://jaeyoung0509.github.io/python-handbook/en/](https://jaeyoung0509.github.io/python-handbook/en/)

## Handbook Architecture

```mermaid
flowchart LR
    A["Intro"] --> B["Pythonic"]
    B --> C["Typing"]
    C --> D["Runtime"]
    D --> E["Asyncio"]
    E --> F["FastAPI"]
    F --> G["Pydantic"]
    G --> H["SQLAlchemy"]
    H --> I["Playbooks"]
    I --> J["Examples and Tests"]
```

## Quick Entry Points

- Korean home: [docs/index.md](docs/index.md)
- English home: [docs/en/index.md](docs/en/index.md)
- Playbooks (Korean): [docs/playbooks/index.md](docs/playbooks/index.md)
- Playbooks (English): [docs/en/playbooks/index.md](docs/en/playbooks/index.md)
- Examples guide: [examples/README.md](examples/README.md)
- Key tests: [tests/test_abc_fake_uow_pytest.py](tests/test_abc_fake_uow_pytest.py), [tests/test_pydantic_settings_patterns.py](tests/test_pydantic_settings_patterns.py), [tests/test_fastapi_fixtures_and_teardown.py](tests/test_fastapi_fixtures_and_teardown.py)

## What This Repository Is

This is not just a note dump or a version changelog.

The goal is to make the repository useful in three ways at once:

- as a readable handbook for learning modern Python 3.14
- as a reference for application architecture and runtime behavior
- as a runnable study workspace with examples, tests, and strict tooling

## Main Sections

- `Intro`: how to read the handbook, the CGI/WSGI/ASGI evolution, and the Python 3.10 to 3.14 transition
- `Pythonic`: data model, descriptors, decorators, context managers, dataclasses, metaclasses
- `Typing`: modern typing, generics, protocols, narrowing, static vs runtime typing
- `Runtime`: execution model, object model, GC, GIL, subinterpreters, specialization
- `Asyncio`: event loop, task groups, cancellation, queues, backpressure, testing
- `FastAPI`: ASGI/Uvicorn, structure, DI, request and response modeling, lifespan, background task boundaries, websockets/streaming, Redis pub/sub, reconnect protocol, proxy and shutdown ops, observability
- `Pydantic`: core schema, validation pipeline, `BaseModel` vs `TypeAdapter`, internals
- `SQLAlchemy`: session/UoW, engine settings, relationships, async usage, migration patterns
- `Playbooks`: settings, testing, UoW, deployment choices, service design patterns

## Repository Layout

```text
docs/        VitePress handbook source
examples/    runnable Python examples
tests/       pytest-based study and architecture tests
.github/     GitHub Actions for docs deployment
.vscode/     workspace settings, including ty-based type checking
```

## Requirements

- Python `3.14+`
- Node.js `20+`
- `uv`
- `npm`

## Quick Start

Install Python dependencies:

```bash
uv sync
```

Install docs tooling:

```bash
npm install
```

Run the docs site locally:

```bash
npm run docs:dev
```

Build the docs site:

```bash
npm run docs:build
```

Run a few example files:

```bash
./.venv/bin/python examples/py310_pattern_matching.py
./.venv/bin/python examples/usecase_with_uow_abc.py
./.venv/bin/python examples/pydantic_settings_patterns.py
```

Run tests:

```bash
uv run pytest
```

## Quality Checks

This repository uses strict static checks.

Type checking:

```bash
uv run ty check
```

Linting:

```bash
uv run ruff check .
```

Tests:

```bash
uv run pytest
```

## VS Code Setup

The workspace is configured to use `ty` instead of `pyright`.

- `.vscode/settings.json` disables the Python language server
- `ty` is used for workspace-wide diagnostics
- Ruff is used for linting

If you open this repository in VS Code and use the project virtual environment, the default workspace setup should already be aligned with the repository tooling.

## Examples and Tests

The handbook is meant to be read with code, not separately from it.

- [`examples/README.md`](examples/README.md) explains what each example demonstrates and when to read it
- `examples/` contains runnable scripts for version features, runtime behavior, FastAPI, SQLAlchemy, dataclasses, settings, and asyncio
- `tests/` contains focused pytest examples for fixtures, settings, and `ABC + Fake UoW` patterns

Good starting points:

- `examples/usecase_with_uow_abc.py`
- `examples/sqlalchemy_deployment_profiles.py`
- `examples/pydantic_settings_patterns.py`
- `tests/test_abc_fake_uow_pytest.py`
- `tests/test_fastapi_fixtures_and_teardown.py`

## Bilingual Docs

The docs site supports both Korean and English.

- Korean pages live under `docs/`
- English pages live under `docs/en/`

The VitePress site is configured with:

- local search
- locale-aware navigation
- custom theme styling
- Mermaid diagrams
- GitHub Pages deployment

## Recommended Reading Order

If you are new to this repository, this order works well:

1. `Intro`
2. `Pythonic`
3. `Typing`
4. `Runtime`
5. `Asyncio`
6. `FastAPI`
7. `Pydantic`
8. `SQLAlchemy`
9. `Playbooks`

If you are already building services, a more practical path is:

1. `Playbooks`
2. `FastAPI`
3. `Pydantic`
4. `SQLAlchemy`
5. `Testing` and deployment-related chapters

## Deployment

The documentation site is deployed with GitHub Pages via GitHub Actions.

- workflow: `.github/workflows/deploy-docs.yml`
- site generator: VitePress
- repository URL: [https://github.com/jaeyoung0509/python-handbook](https://github.com/jaeyoung0509/python-handbook)

## Notes

- The Python project metadata still uses the package name `python-deep` in `pyproject.toml`, while the documentation site branding is `Python Handbook`.
- The repository is optimized for handbook content and study examples rather than for packaging as a reusable Python library.
