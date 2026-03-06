# Import, Packaging, and Environment

<p class="lead">In Python, imports, package layout, build metadata, and virtual environments are not separate concerns. Together they decide how code is found, how it is installed, and which interpreter actually runs it. If this layer stays fuzzy, teams keep rediscovering the same failures: circular imports, confusion around `python -m`, editable-install illusions, and code that works locally but breaks after deployment.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: the import system builds the executable module graph, packaging builds installable artifacts, and virtual environments isolate dependency sets. Most Python project bugs appear when those layers are mentally collapsed into one.</p>
</div>

<MermaidDiagram
  caption="Running Python is not just opening a file. Interpreter startup, `sys.path`, module specs, loaders, and package metadata all participate."
  chart="flowchart LR; A[&quot;Interpreter startup&quot;] --> B[&quot;sys.path construction&quot;]; B --> C[&quot;finder / loader&quot;]; C --> D[&quot;module spec&quot;]; D --> E[&quot;sys.modules cache&quot;]; E --> F[&quot;package import or entry point&quot;]; F --> G[&quot;runtime side effects&quot;];"
/>

## Why this layer matters

- `import` is not file inclusion; it creates and caches module objects.
- package layout changes which imports succeed and from where.
- `pyproject.toml` declares build metadata, backend choice, and entry points.
- `venv` changes which site-packages tree and scripts the interpreter sees.

That means a Python project is not understood fully by reading the source tree alone. You also need the interpreter's rules for reading that tree.

## 1) Execution context: `python file.py` and `python -m package.module` are different

This distinction explains many relative-import surprises.

| Execution mode | `sys.path[0]` anchor | Package context | Common use |
| --- | --- | --- | --- |
| `python script.py` | the script's directory | weak | one-off scripts, quick experiments |
| `python -m package.module` | the current working directory | strong | running code inside a package |
| console script entry point | the installed wrapper | strong | deployed CLIs |

```py
# src/myapp/cli.py
from .service import main

if __name__ == "__main__":
    main()
```

If you execute `cli.py` directly as a file path, `from .service import main` may fail. If you run `python -m myapp.cli`, Python sets up package context first, so the same import works.

<p class="code-caption">Python uses a different import anchor when it runs a path versus a module. Once application code lives inside a package, it is safer to think in terms of `python -m ...` and console scripts than raw file execution.</p>

## 2) What the import system actually does

At a high level, `import x` usually means:

1. Check `sys.modules` for an existing module object.
2. If absent, ask a finder for a module spec.
3. Let a loader create and execute the module.
4. Keep the resulting module object in `sys.modules`.

### `sys.modules`: the import cache

- Inside one process, a module's top-level code normally executes once.
- Re-importing usually reuses the existing module object.
- `importlib.reload()` is a specialized tool, not a structural fix.

That cache is why heavy top-level side effects make startup order and import order leak into application behavior.

### `sys.path`: where Python is allowed to look

`sys.path` is commonly assembled from:

- the script directory or current working directory
- standard library paths
- the active interpreter's site-packages
- `PYTHONPATH`, if present

The crucial point is that "the project root you think you are in" and "the paths Python is actually importing from" are not always the same thing.

## 3) Why circular imports happen

The core issue is not merely that two files import each other. The issue is that one module asks for names from another while that other module is only partially initialized.

### Typical failure shape

```py
# users/service.py
from users.repository import UserRepository

SERVICE_NAME = "users"
```

```py
# users/repository.py
from users.service import SERVICE_NAME
```

If `repository.py` reaches into `service.py` before `service.py` has finished executing, Python exposes a partially initialized module.

### Better fixes most of the time

- Move shared constants or types into a separate module.
- Revisit module boundaries before hiding imports inside functions.
- Prevent routes, services, repositories, and schemas from forming cycles.

Function-local imports can be a tactical escape hatch, but they often hide a structural problem.

## 4) Package layout: why `src/` is often the safer default

```text
project/
  pyproject.toml
  src/
    myapp/
      __init__.py
      __main__.py
      cli.py
      service.py
  tests/
```

The biggest benefit of a `src/` layout is that it forces a distinction between "installed package" and "current working directory".

### Why `src/` helps

- It exposes imports that only worked accidentally from the repo root.
- It makes editable-install assumptions more visible.
- It reduces the chance that tests silently import from the source tree instead of the installed package.

### When `__init__.py` matters

- Keep it for a traditional package.
- Omit it only if you intentionally want a namespace package.
- For most service codebases, explicit `__init__.py` files are easier to reason about.

Namespace packages are powerful, but they also make import reasoning and tooling configuration more subtle.

## 5) `pyproject.toml`: the modern contract for a Python project

Modern packaging now centers on `pyproject.toml`.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["fastapi>=0.135", "sqlalchemy>=2.0"]

[project.scripts]
myapp = "myapp.cli:main"
```

This file defines:

- which build backend is used
- the project's installable metadata
- the required Python version
- the CLI entry points

### wheel vs sdist

| Artifact | Meaning | When it matters |
| --- | --- | --- |
| wheel | built install artifact | repeatable installs, faster deployment |
| sdist | source distribution | build validation, source-based release paths |

In real systems the question is not "does it work on my laptop?", but "does the built wheel install the same way everywhere?".

### What editable install really means

Editable install (PEP 660) loosely links the source tree into the environment. That is convenient during development, but it can create the illusion that packaging details do not matter because imports appear to work immediately.

Editable install is a convenience mechanism, not a replacement for packaging discipline.

## 6) What virtual environments isolate and what they do not

`venv` isolates the interpreter view of installed packages and scripts.

- It isolates: package set, interpreter path, generated script wrappers
- It does not isolate: the operating system process model, filesystem contents, environment variables themselves, or network access

### What matters in practice

- `sys.prefix != sys.base_prefix` usually means a virtual environment is active.
- `python -c "import sys; print(sys.executable)"` is often more trustworthy than `which python`.
- Always verify that VS Code, pytest, CI, and your shell are using the same interpreter.

## 7) How entry points turn into CLIs

If you declare:

```toml
[project.scripts]
myapp = "myapp.cli:main"
```

installation creates a `myapp` wrapper script. That wrapper selects the right interpreter and import path, then calls `myapp.cli:main`.

That is why production CLIs are usually safer when designed around entry points than around `python some/file.py`.

## 8) The places teams break most often

### Import-related failures

- top-level code opens DB connections, performs HTTP calls, or loads heavy settings immediately
- routes and repositories import each other
- tests succeed only because the working directory accidentally helps imports

### Packaging-related failures

- `pyproject.toml` metadata and package layout drift apart
- CLIs are designed for file execution but deployed as console scripts
- editable install is the only thing ever tested

### Environment-related failures

- the shell Python, editor Python, and CI Python are not the same
- a team uses `.venv` but never confirms that `uv run`, `pytest`, and `python` resolve to the same interpreter

## Working rules

<div class="doc-checklist">
  <div class="check-card">
    <h3>Treat `src/` layout as the default</h3>
    <p>It separates installation from local path accidents.</p>
  </div>
  <div class="check-card">
    <h3>Application code should also run via `python -m`</h3>
    <p>Do not rely on file-path execution for package-internal imports.</p>
  </div>
  <div class="check-card">
    <h3>Minimize top-level side effects</h3>
    <p>Keep import time separate from runtime initialization.</p>
  </div>
  <div class="check-card">
    <h3>Validate wheel installation at least once</h3>
    <p>Do not assume editable install proves packaging correctness.</p>
  </div>
</div>

## Good companion chapters in this repository

1. [Execution Model](/en/runtime/execution-model)
2. [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings)
3. [ASGI and Uvicorn](/en/fastapi/asgi-and-uvicorn)

For runnable intuition, pair this with `examples/import_packaging_environment_lab.py`.

## Official References

- [The import system](https://docs.python.org/3/reference/import.html)
- [importlib](https://docs.python.org/3/library/importlib.html)
- [venv](https://docs.python.org/3/library/venv.html)
- [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PEP 451 - A ModuleSpec Type for the Import System](https://peps.python.org/pep-0451/)
- [PEP 517 - Build-system independent format](https://peps.python.org/pep-0517/)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 660 - Editable installs](https://peps.python.org/pep-0660/)
