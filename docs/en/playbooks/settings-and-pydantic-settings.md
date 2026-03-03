# Settings and Pydantic Settings

<p class="lead">Once service code starts calling `os.getenv()` everywhere, it becomes unclear which settings are required, which are secrets, how tests should override them, and which source wins in each deployment environment. `settings.py` is not just convenience code. It is a configuration boundary.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: build one typed settings object with `pydantic-settings`, understand the source order as `init args -> env -> dotenv -> secrets -> defaults`, and inject that object into the app. Environment lookups should stay inside `settings.py`, not leak across the codebase.</p>
</div>

## The Big Picture

<MermaidDiagram
  caption="Environment variables, dotenv files, secret files, and test overrides should meet only inside the settings boundary. The rest of the app sees a typed settings object."
  chart="flowchart LR; A[init kwargs] --> E[AppSettings]; B[environment variables] --> E; C[dotenv file] --> E; D[secret files] --> E; E --> F[get_settings cache]; F --> G[FastAPI dependency or app factory];"
/>

## Why `settings.py` Exists

- it makes required and optional settings explicit in types
- it models secret and non-secret values differently
- it gives tests one place to override configuration
- it makes deployment source priority easier to reason about

## Suggested Structure

```text
app/
  core/
    settings.py
    logging.py
  db/
    session.py
  main.py
tests/
  test_pydantic_settings_patterns.py
```

## Recommended Model Shape

```py
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_nested_delimiter="__",
        validate_default=True,
    )

    environment: Literal["local", "test", "staging", "prod"] = "local"
    debug: bool = False
    database: DatabaseSettings
    auth_token: SecretStr
    sentry_dsn: str | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_SENTRY_DSN", "SENTRY_DSN"),
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
```

<p class="code-caption">Three choices matter most here: `env_prefix` namespaces the service, `env_nested_delimiter` makes nested config readable, and `@lru_cache` keeps settings instantiation aligned with app lifetime.</p>

## Source Priority Drives Operational Behavior

Read the default order like this:

1. direct initialization values passed to `AppSettings(...)`
2. real environment variables
3. `.env` files
4. secret-file directories
5. code defaults

That implies:

- production env vars beat local dotenv values
- tests can override dotenv values cleanly with `monkeypatch.setenv()`
- secret files are a good fallback source when env vars are absent

## Recommended Operational Defaults

| Environment | Primary source | Secondary source | Usually avoid |
| --- | --- | --- | --- |
| local development | `.env` | shell env | copying production secrets into local files |
| CI and tests | init kwargs, `monkeypatch.setenv()` | test-only env files | depending on a developer's local `.env` |
| Kubernetes | env vars, secret volume or manager | config map | baking `.env` into the image |
| Lambda | env vars, Secrets Manager or Parameter Store | init override | shipping large dotenv bundles |

## Use `validation_alias` and `AliasChoices` for Migration, Not Forever

```py
sentry_dsn: str | None = Field(
    default=None,
    validation_alias=AliasChoices("APP_SENTRY_DSN", "SENTRY_DSN"),
)
```

- this lets old and new variable names coexist briefly
- it is excellent for staged renames
- it should not become a permanent pile of aliases

## How to Test Settings

```py
def test_env_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_DATABASE__HOST=dotenv-db\n", encoding="utf-8")
    monkeypatch.setenv("APP_DATABASE__HOST", "env-db")

    settings = AppSettings(
        _env_file=env_file,
        database={"port": 5432},
        auth_token="token",
    )

    assert settings.database.host == "env-db"
```

The `tmp_path`, `monkeypatch`, `_env_file`, and `_secrets_dir` combination is extremely effective for configuration tests. This repository includes that pattern in `tests/test_pydantic_settings_patterns.py`.

## Avoid These Settings Patterns

- scattering `os.getenv()` across services, routes, and repositories
- constructing `Settings()` over and over inside request paths
- treating `.env` as the primary production source
- mixing runtime state with static configuration
- leaking secrets around as plain `str` values by default

## Examples in This Repository

- runnable example: `examples/pydantic_settings_patterns.py`
- test example: `tests/test_pydantic_settings_patterns.py`
- structural companion: [API Service Template](/en/playbooks/api-service-template)

## Official References

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
