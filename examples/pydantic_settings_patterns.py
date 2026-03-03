# Settings patterns with pydantic-settings.
# pydantic-settings 기반 settings 패턴 예제.
# Why: configuration should be a typed boundary, not scattered os.getenv calls.
# 왜: 설정은 흩어진 os.getenv 호출이 아니라 타입이 있는 경계여야 한다.
# Use when: designing settings.py for FastAPI, workers, or CLI tools.
# 언제 쓰나: FastAPI, worker, CLI용 settings.py 경계를 설계할 때 적합하다.

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
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
def get_settings(*, env_file: Path, secrets_dir: Path) -> AppSettings:
    return AppSettings(  # ty: ignore[missing-argument]
        _env_file=env_file,  # ty: ignore[unknown-argument]
        _secrets_dir=secrets_dir,  # ty: ignore[unknown-argument]
    )


@contextmanager
def temporary_environ(values: Mapping[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def main() -> None:
    with TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        env_file = temp_dir / ".env"
        secrets_dir = temp_dir / "secrets"
        secrets_dir.mkdir()

        env_file.write_text(
            "\n".join(
                [
                    "APP_ENVIRONMENT=staging",
                    "APP_DATABASE__HOST=dotenv-db",
                    "APP_DATABASE__PORT=5433",
                ]
            ),
            encoding="utf-8",
        )
        (secrets_dir / "app_auth_token").write_text("secret-from-file", encoding="utf-8")

        with temporary_environ(
            {
                "APP_DATABASE__HOST": "env-db",
                "SENTRY_DSN": "https://sentry.example/project",
            }
        ):
            get_settings.cache_clear()
            settings = get_settings(env_file=env_file, secrets_dir=secrets_dir)
            cached_again = get_settings(env_file=env_file, secrets_dir=secrets_dir)

            print("same cached object:", settings is cached_again)
            print("environment:", settings.environment)
            print("database host:", settings.database.host)
            print("database port:", settings.database.port)
            print("auth token masked:", settings.auth_token)
            print("sentry dsn:", settings.sentry_dsn)

            # Environment variables override dotenv files.
            # 환경 변수는 dotenv 파일보다 우선한다.
            print("env overrides dotenv:", settings.database.host == "env-db")


if __name__ == "__main__":
    main()
