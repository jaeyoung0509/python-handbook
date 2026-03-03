# Settings와 Pydantic Settings

<p class="lead">서비스 코드 전체가 `os.getenv()`를 직접 읽기 시작하면, 어떤 값이 필수인지, 어떤 값이 secret인지, 테스트에서 무엇을 바꿔야 하는지, 배포 환경마다 source priority가 어떻게 다른지가 모두 흐려진다. `settings.py`는 단순 convenience가 아니라 "설정 경계"다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: `pydantic-settings`로 하나의 typed settings object를 만들고, source priority는 `init args -> env -> dotenv -> secrets -> defaults`로 이해한다. 앱 코드는 settings object를 주입받고, 환경 변수 읽기는 `settings.py` 한 군데로 몰아야 한다.</p>
</div>

## 큰 그림

<MermaidDiagram
  caption="환경변수, .env, secret 파일, 테스트 override는 모두 settings boundary에서만 만나야 한다. 앱 나머지는 typed settings object만 본다."
  chart="flowchart LR; A[init kwargs] --> E[AppSettings]; B[environment variables] --> E; C[dotenv file] --> E; D[secret files] --> E; E --> F[get_settings cache]; F --> G[FastAPI dependency or app factory];"
/>

## 왜 `settings.py`가 필요한가

- 필수 설정과 선택 설정을 타입으로 고정할 수 있다.
- `SecretStr`, `Literal`, nested model로 설정 shape를 명확히 드러낼 수 있다.
- 테스트에서 dependency override나 `monkeypatch.setenv()` 지점을 한 곳으로 좁힐 수 있다.
- 운영 환경 source priority를 문서화하고 검증하기 쉬워진다.

## 추천 구조

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

## 추천 모델 구조

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

<p class="code-caption">여기서 중요한 점은 세 가지다. `env_prefix`로 서비스 namespace를 고정하고, `env_nested_delimiter`로 nested config를 표현하고, `@lru_cache`로 app lifetime 동안 설정 객체를 한 번만 만든다.</p>

## source priority를 이해해야 운영이 덜 꼬인다

기본 우선순위는 보통 이 순서로 읽으면 된다.

1. `AppSettings(...)`에 직접 넘긴 초기값
2. 실제 환경 변수
3. `.env` 파일
4. secret 파일 디렉터리
5. 코드 기본값

이 의미는 분명하다.

- 운영에서 환경 변수는 `.env`보다 우선한다.
- 테스트에서 `_env_file=...`를 넘겨도 `monkeypatch.setenv()`가 더 강하다.
- secret file은 fallback source로 쓰기 좋다.

## 운영 기준 추천

| 환경 | 주 소스 | 보조 소스 | 보통 하지 않는 것 |
| --- | --- | --- | --- |
| local dev | `.env` | shell env | 운영 secret 복붙 |
| CI/test | init kwargs, `monkeypatch.setenv()` | test-only env file | 로컬 `.env`에 의존 |
| Kubernetes | env vars, secret volume/manager | config map | 이미지 안 `.env` 고정 |
| Lambda | env vars, Secrets Manager/Parameter Store | init override | 큰 `.env` 묶음 주입 |

## `validation_alias`와 `AliasChoices`는 마이그레이션용으로 쓴다

이 패턴은 특히 설정 이름을 옮기는 과도기에서 유용하다.

```py
sentry_dsn: str | None = Field(
    default=None,
    validation_alias=AliasChoices("APP_SENTRY_DSN", "SENTRY_DSN"),
)
```

- 새 이름과 옛 이름을 둘 다 읽을 수 있다.
- 하지만 영구적으로 alias를 쌓아두면 설정 규칙이 흐려진다.
- migration 기간이 끝나면 오래된 이름은 제거하는 편이 좋다.

## 테스트에서는 이렇게 다룬다

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

`tmp_path`, `monkeypatch`, `_env_file`, `_secrets_dir` 조합은 설정 테스트에서 매우 강력하다. 이 저장소에는 `tests/test_pydantic_settings_patterns.py`로 넣어두었다.

## `settings.py`에서 하지 않는 편이 좋은 것

- 서비스 코드 곳곳에서 `os.getenv()`를 직접 읽는 것
- `Settings()`를 route나 repository에서 매번 새로 만드는 것
- `.env`를 production의 주 source로 삼는 것
- runtime state와 config state를 같은 객체에 섞는 것
- secret을 평문 `str`로 마구 흘리는 것

## 이 저장소의 예제

- 실행 예제: `examples/pydantic_settings_patterns.py`
- 테스트 예제: `tests/test_pydantic_settings_patterns.py`
- 앱 구조 문서: [API Service Template](/playbooks/api-service-template)

## 공식 자료

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
