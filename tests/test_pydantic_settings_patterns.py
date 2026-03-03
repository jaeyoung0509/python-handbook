from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
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
    database: DatabaseSettings
    auth_token: SecretStr
    sentry_dsn: str | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_SENTRY_DSN", "SENTRY_DSN"),
    )


def test_environment_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENVIRONMENT=staging",
                "APP_DATABASE__HOST=dotenv-db",
                "APP_DATABASE__PORT=5433",
                "APP_AUTH_TOKEN=dotenv-token",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("APP_DATABASE__HOST", "env-db")
    monkeypatch.setenv("SENTRY_DSN", "https://sentry.example/project")

    settings = AppSettings(_env_file=env_file)  # ty: ignore[missing-argument, unknown-argument]

    assert settings.environment == "staging"
    assert settings.database.host == "env-db"
    assert settings.database.port == 5433
    assert settings.auth_token.get_secret_value() == "dotenv-token"
    assert settings.sentry_dsn == "https://sentry.example/project"


def test_secret_dir_is_used_when_env_is_missing(tmp_path: Path) -> None:
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "app_auth_token").write_text("secret-from-file", encoding="utf-8")

    settings = AppSettings(  # ty: ignore[missing-argument]
        _env_file=None,  # ty: ignore[unknown-argument]
        _secrets_dir=secrets_dir,  # ty: ignore[unknown-argument]
        database=DatabaseSettings(host="db.internal", port=5432),
    )

    assert settings.database.host == "db.internal"
    assert settings.auth_token.get_secret_value() == "secret-from-file"
