# Examples

이 디렉터리는 핸드북 문서를 "읽고 끝내는 것"이 아니라 바로 실행해보며 감을 잡도록 만든 예제 모음이다. 예제는 크게 두 축으로 나뉜다.

- 버전별 변화 예제: Python 3.10~3.14에서 새로 들어온 기능을 빠르게 체감
- 주제별 심화 예제: Pydantic, asyncio, FastAPI, SQLAlchemy, dataclass, testing 같은 실전 주제를 코드로 확인

모든 예제는 이 저장소의 `.venv` 기준으로 점검한다.

## 실행 방법

개별 실행:

```bash
./.venv/bin/python examples/py310_pattern_matching.py
./.venv/bin/python examples/pydantic_validation_pipeline.py
./.venv/bin/python examples/fastapi_service_template_example.py
```

전체 순회:

```bash
for file in examples/*.py; do
  echo "=== $file ==="
  ./.venv/bin/python "$file"
done
```

정적 검사:

```bash
uv run ty check
uv run ruff check .
```

## 핸드북 파트별 추천 예제

| 파트 | 먼저 볼 예제 | 왜 먼저 보나 |
| --- | --- | --- |
| Pythonic | `py310_pattern_matching.py`, `metaprogramming_hooks_lab.py` | Python 문법의 표현력과 메타프로그래밍 훅 선택 감각을 함께 익히기 좋음 |
| Typing | `py310_typing_and_zip_strict.py`, `py312_type_params.py` | modern typing 문법과 boundary 설계 감각을 같이 잡기 좋음 |
| Runtime | `py312_sys_monitoring.py`, `py313_runtime_modes.py`, `py314_interpreter_pool.py`, `cpython_runtime_labs.py` | CPython 런타임 방향성과 내부 실험(dis/ast/gc/tracemalloc)을 함께 보여줌 |
| Dataclass | `dataclass_patterns.py` | 값 객체, `default_factory`, `kw_only`, 패턴 매칭 조합을 빨리 익히기 좋음 |
| Asyncio | `py311_exception_groups_and_taskgroup.py`, `asyncio_backpressure_and_cancellation.py` | 구조적 동시성, cancellation, backpressure를 함께 익히기 좋음 |
| Pydantic | `pydantic_validation_pipeline.py` | core schema, strict/lax, validator/serializer 흐름을 한 번에 보여줌 |
| FastAPI / SQLAlchemy | `asgi_lifecycle_lab.py`, `fastapi_background_tasks_patterns.py`, `fastapi_realtime_and_middleware_lab.py`, `websocket_auth_and_rooms_lab.py`, `uvicorn_proxy_and_health_lab.py`, `fastapi_service_template_example.py`, `sqlalchemy_loading_strategies.py`, `sqlalchemy_class_based_uow.py`, `usecase_with_uow_abc.py`, `sqlalchemy_deployment_profiles.py` | ASGI 메시지 흐름, BackgroundTasks 경계, realtime transport, websocket 실전 패턴, middleware, proxy/health, 서비스 경계, ORM 로딩 전략, class-based UoW, ABC 기반 use case, 배포별 엔진 설정 감각을 같이 확인할 수 있음 |
| Settings | `pydantic_settings_patterns.py` | `settings.py`, env source priority, `.env`, secrets, `pydantic-settings` 감각을 빠르게 익히기 좋음 |
| Testing | `tests/test_fastapi_fixtures_and_teardown.py` | fixture setup/teardown, override cleanup, TestClient lifecycle을 실제 테스트로 확인 |

## 버전별 예제 맵

| 버전 | 파일 | 핵심 기능 | 볼 포인트 |
| --- | --- | --- | --- |
| 3.10 | `py310_pattern_matching.py` | `match/case` | 데이터 모양 기반 분기가 얼마나 간결해지는지 |
| 3.10 | `py310_typing_and_zip_strict.py` | `ParamSpec`, `TypeGuard`, `zip(strict=True)` | 타입 정밀도와 조용한 데이터 손실 방지 |
| 3.11 | `py311_exception_groups_and_taskgroup.py` | `TaskGroup`, `ExceptionGroup`, `except*` | 구조적 동시성과 구조적 실패 처리 |
| 3.11 | `py311_tomllib.py` | `tomllib` | 표준 라이브러리 TOML 파싱 |
| 3.12 | `py312_type_params.py` | type parameter syntax, `type` alias | typing 문법의 언어화 |
| 3.12 | `py312_sys_monitoring.py` | `sys.monitoring` | 저비용 런타임 이벤트 훅 |
| 3.13 | `py313_runtime_modes.py` | free-threaded/JIT 상태 조회 | CPython 런타임 방향성 |
| 3.13 | `py313_type_defaults_and_deprecated.py` | type defaults, `warnings.deprecated` | 제네릭 사용성과 deprecation 신호 |
| 3.14 | `py314_annotationlib.py` | `annotationlib` | 어노테이션 introspection 변화 |
| 3.14 | `py314_template_strings.py` | `t"..."`, `string.templatelib` | 문자열 결과가 아니라 템플릿 구조 다루기 |
| 3.14 | `py314_interpreter_pool.py` | `InterpreterPoolExecutor` | subinterpreter 기반 병렬성 |

## 주제별 심화 예제

### `pydantic_validation_pipeline.py`

무엇을 보여주나:

- `TypeAdapter`와 `BaseModel`의 공통 엔진
- strict vs lax parsing
- validator와 serializer 역할 분리
- `TypedDict` 같은 임의 타입 구조 검증

언제 보면 좋나:

- Pydantic handbook 파트를 읽은 직후
- FastAPI request/response DTO를 더 정교하게 설계하고 싶을 때

### `asyncio_backpressure_and_cancellation.py`

무엇을 보여주나:

- `TaskGroup`
- bounded queue
- `Semaphore`
- `Queue.shutdown()`
- cancellation path cleanup

언제 보면 좋나:

- asyncio chapter에서 cancellation/backpressure를 읽은 직후
- worker, fan-out pipeline, webhook consumer 구조를 고민할 때

### `dataclass_patterns.py`

무엇을 보여주나:

- `frozen=True`, `slots=True`, `kw_only=True`
- `default_factory`
- `__post_init__()` 정규화
- dataclass와 pattern matching 조합

언제 보면 좋나:

- Pythonic 파트에서 dataclass 챕터를 읽은 직후
- 내부 command/value object를 어떻게 만들지 고민할 때

실행:

```bash
./.venv/bin/python examples/dataclass_patterns.py
```

### `metaprogramming_hooks_lab.py`

무엇을 보여주나:

- `__set_name__` descriptor binding
- `__init_subclass__` 등록 패턴
- class decorator 후처리
- metaclass 정책 강제

왜 중요한가:

- 메타프로그래밍에서 "가장 작은 도구부터 고르는 기준"을 실행 코드로 체감할 수 있다.
- 선언형 API를 만들 때 어느 훅을 써야 팀 비용이 낮은지 감이 생긴다.

실행:

```bash
./.venv/bin/python examples/metaprogramming_hooks_lab.py
```

체크 포인트:

- descriptor가 attribute access를 제어한다.
- subclass 등록이 metaclass 없이도 가능하다.
- class decorator와 metaclass의 책임 차이가 보인다.

### `asgi_lifecycle_lab.py`

무엇을 보여주나:

- `scope`, `receive`, `send`
- `lifespan.startup` / `lifespan.shutdown`
- `http.response.start` / `http.response.body`
- ASGI app이 response object 대신 message를 보내는 구조

왜 중요한가:

- FastAPI가 "어떤 request object를 직접 받는 프레임워크"가 아니라 ASGI contract 위에 올라간다는 점이 선명해진다.
- `CGI -> WSGI -> ASGI` 역사에서 왜 ASGI가 connection/event 모델로 바뀌었는지 코드로 체감할 수 있다.

실행:

```bash
./.venv/bin/python examples/asgi_lifecycle_lab.py
```

체크 포인트:

- lifespan과 http가 다른 scope type으로 보인다.
- 앱은 event를 `receive()`로 읽고 `send()`로 response message를 쓴다.
- Uvicorn 같은 ASGI server가 실제로 하는 역할을 추상적으로 이해할 수 있다.

### `fastapi_background_tasks_patterns.py`

무엇을 보여주나:

- `BackgroundTasks` + sync task
- `BackgroundTasks` + async task
- inline await가 필요한 작업
- queue/worker로 빼야 하는 작업 분류

왜 중요한가:

- "동기 함수를 background에 넣어도 되는가", "async로 감싸면 해결되는가" 같은 실무 질문에 기준선을 준다.
- `BackgroundTasks`가 durable queue가 아니라는 점을 코드와 출력으로 같이 확인할 수 있다.

실행:

```bash
./.venv/bin/python examples/fastapi_background_tasks_patterns.py
```

체크 포인트:

- audit log는 `background-sync`로 분류된다.
- async webhook은 `background-async`로 분류된다.
- invoice PDF 같은 일은 `queue-worker`로 분류된다.
- 결제 승인처럼 응답에 영향을 주는 일은 `inline-await`로 남는다.

### `fastapi_realtime_and_middleware_lab.py`

무엇을 보여주나:

- `StreamingResponse`
- SSE (`text/event-stream`)
- WebSocket echo
- pure ASGI middleware가 HTTP와 WebSocket scope를 보는 방식

왜 중요한가:

- realtime transport를 "그냥 route 종류 하나 더"가 아니라 연결 수명 모델로 이해하게 해준다.
- middleware가 request object보다 더 아래 ASGI 레벨에서 어떻게 응답 header를 다루는지 보인다.

실행:

```bash
./.venv/bin/python examples/fastapi_realtime_and_middleware_lab.py
```

체크 포인트:

- plain stream과 SSE의 `content-type`이 다르다.
- WebSocket은 별도 메시지 loop를 가진다.
- pure ASGI middleware는 HTTP와 WebSocket scope를 모두 관찰한다.

### `uvicorn_proxy_and_health_lab.py`

무엇을 보여주나:

- `root_path`
- `TrustedHostMiddleware`
- `HTTPSRedirectMiddleware`
- readiness 전환
- 배포 프로필별 Uvicorn 플래그 감각

왜 중요한가:

- 로컬에서는 멀쩡한데 proxy 뒤 배포에서 어긋나는 문제를 어디서 봐야 하는지 감을 준다.
- readiness를 내려서 drain하는 종료 흐름과 host/scheme 보호 장치를 같이 볼 수 있다.

실행:

```bash
./.venv/bin/python examples/uvicorn_proxy_and_health_lab.py
```

체크 포인트:

- HTTP 요청은 HTTPS redirect를 받는다.
- `root_path`가 scope에 들어간다.
- drain 뒤 readiness가 `503`으로 내려간다.
- 허용되지 않은 host는 거부된다.

### `websocket_auth_and_rooms_lab.py`

무엇을 보여주나:

- connect 시 token 인증
- `RoomManager`의 join/leave/broadcast
- room 내부 fan-out
- disconnect cleanup
- invalid token close code

왜 중요한가:

- echo server 수준을 넘어 실제 서비스에서 가장 먼저 필요한 websocket 기본형을 보여준다.
- route loop에 auth/room 상태/cleanup을 다 몰아넣지 않고 역할을 분리하는 감각을 준다.

실행:

```bash
./.venv/bin/python examples/websocket_auth_and_rooms_lab.py
```

체크 포인트:

- 첫 연결은 `system:...:joined` 메시지를 받는다.
- 두 번째 연결이 들어오면 room fan-out이 양쪽에 전달된다.
- disconnect 뒤 room state가 정리된다.
- 잘못된 token은 policy violation close code로 끊긴다.

### `fastapi_service_template_example.py`

무엇을 보여주나:

- route는 HTTP 계약만 소유
- service가 transaction 경계를 소유
- repository가 query와 persistence 세부 구현 담당
- response DTO로 API 계약 마무리

왜 중요한가:

- "작동은 하는데 금방 지저분해지는" FastAPI 구조를 피하는 기본 패턴을 실행 가능한 형태로 볼 수 있다.
- `commit`과 `flush`가 어디 있어야 하는지 감이 생긴다.

실행:

```bash
./.venv/bin/python examples/fastapi_service_template_example.py
```

체크 포인트:

- 첫 요청은 `201`로 생성된다.
- 같은 이메일로 다시 요청하면 `409`가 반환된다.
- 조회는 `GET /users/1`로 별도 route를 통해 이뤄진다.

### `sqlalchemy_class_based_uow.py`

무엇을 보여주나:

- class-based `SqlAlchemyUnitOfWork`
- repository 묶음과 session 소유권
- service가 commit 시점만 결정하는 패턴

왜 중요한가:

- repository가 많아질수록 "한 작업 단위"를 명시적 객체로 두는 편이 읽기 좋아질 때가 있다.
- session을 직접 흘리는 방식과 UoW 객체를 주입하는 방식의 차이를 체감할 수 있다.

실행:

```bash
./.venv/bin/python examples/sqlalchemy_class_based_uow.py
```

체크 포인트:

- 중복 이메일은 `DuplicateEmail`로 막힌다.
- `flush()`는 commit 전에 PK를 확보한다.
- UoW가 session close를 소유한다.

### `usecase_with_uow_abc.py`

무엇을 보여주나:

- `abc.ABC` 기반 port
- use case가 concrete SQLAlchemy 대신 UoW port에 의존하는 구조
- commit 뒤 외부 부수효과를 실행하는 패턴

왜 중요한가:

- SOLID의 DIP를 Python 서비스 코드에 어떻게 "과하지 않게" 적용할지 보여준다.
- 모든 계층을 interface로 만드는 나쁜 패턴과, 진짜 경계만 추상화하는 좋은 패턴 차이를 이해하기 좋다.
- 팀이 `Protocol`보다 명시적 abstract base class를 선호할 때 어떤 모양이 읽기 좋은지 바로 볼 수 있다.

실행:

```bash
./.venv/bin/python examples/usecase_with_uow_abc.py
```

체크 포인트:

- 첫 등록 뒤 welcome notifier가 실행된다.
- 중복 이메일은 `DuplicateEmail`로 막힌다.
- use case는 notifier와 UoW ABC만 알고, SQLAlchemy 세부 구현은 바깥에 남는다.

### `sqlalchemy_deployment_profiles.py`

무엇을 보여주나:

- Lambda direct DB
- Lambda + RDS Proxy
- Kubernetes sync API
- Kubernetes async API
- batch/worker

왜 중요한가:

- SQLAlchemy 설정은 배포 환경의 process model에 따라 달라져야 한다.
- `pool_size`, `max_overflow`가 DB connection budget에 어떤 영향을 주는지 감을 잡기 좋다.

실행:

```bash
./.venv/bin/python examples/sqlalchemy_deployment_profiles.py
```

체크 포인트:

- 환경별로 `QueuePool`과 `NullPool` 선택이 어떻게 달라지는지 본다.
- session 기본값으로 `autoflush=False`, `expire_on_commit=False`를 왜 자주 쓰는지 확인한다.
- Kubernetes 예시에서 총 연결 수 계산을 직접 본다.

### `pydantic_settings_patterns.py`

무엇을 보여주나:

- `pydantic-settings`
- `env_prefix`
- `env_nested_delimiter`
- `.env`와 실제 환경 변수 우선순위
- secret dir와 `@lru_cache`

왜 중요한가:

- 서비스 설정은 코드 곳곳의 `os.getenv()`가 아니라 typed boundary로 다뤄야 한다.
- local, test, Kubernetes, Lambda에서 source priority를 어떻게 이해해야 하는지 감을 잡기 좋다.

실행:

```bash
./.venv/bin/python examples/pydantic_settings_patterns.py
```

체크 포인트:

- 같은 인자로 `get_settings()`를 두 번 부르면 cache hit가 난다.
- 실제 환경 변수가 `.env`보다 우선한다.
- secret 값은 secret dir fallback으로도 공급될 수 있다.

### `sqlalchemy_loading_strategies.py`

무엇을 보여주나:

- 기본 lazy loading
- `selectinload()`
- `joinedload()`
- 각 전략별 query count 차이

왜 중요한가:

- SQLAlchemy 성능 문제는 ORM 문법보다 loading strategy에서 더 자주 발생한다.
- 목록 API와 상세 API가 왜 다른 로딩 전략을 가져야 하는지 직관적으로 보인다.

실행:

```bash
./.venv/bin/python examples/sqlalchemy_loading_strategies.py
```

체크 포인트:

- lazy loading은 부모 조회 후 관계 접근 때 추가 쿼리가 발생한다.
- `selectinload()`는 대체로 2번 쿼리로 안정적인 목록 로딩을 보여준다.
- `joinedload()`는 한 번의 쿼리지만 collection에서는 `unique()` 처리가 필요하다.

### `cpython_runtime_labs.py`

무엇을 보여주나:

- `ast.parse()`와 AST dump
- `dis.dis()` 바이트코드 관찰
- cycle 객체 + `gc.collect()`
- `tracemalloc` 상위 할당 라인 추적
- `sys.monitoring` 이벤트 샘플

왜 중요한가:

- CPython 내부 동작을 개념이 아니라 관찰 가능한 실험으로 이해할 수 있다.
- runtime 파트 학습 후 "어디서 비용이 생기는지"를 직접 확인하기 좋다.

실행:

```bash
./.venv/bin/python examples/cpython_runtime_labs.py
```

체크 포인트:

- 함수 실행이 bytecode 형태로 보인다.
- cycle GC가 refcount와 다른 역할을 한다.
- 할당 hotspot을 파일/라인 기준으로 볼 수 있다.

## 테스트 예제

### `tests/test_fastapi_fixtures_and_teardown.py`

무엇을 보여주나:

- engine fixture setup/teardown
- seed fixture
- FastAPI `dependency_overrides` cleanup
- `TestClient` context manager lifecycle

실행:

```bash
uv run pytest tests/test_fastapi_fixtures_and_teardown.py
```

체크 포인트:

- seed 데이터가 fixture에서 준비된다.
- `/meta`는 override된 dependency 값 `"test"`를 본다.
- teardown은 fixture 쪽에서 소유하고 test body는 소비만 한다.

### `tests/test_abc_fake_uow_pytest.py`

무엇을 보여주나:

- `abc.ABC` 기반 경계
- `FakeUnitOfWork`
- `RecordingNotifier`
- pytest fixture graph

실행:

```bash
uv run pytest tests/test_abc_fake_uow_pytest.py
```

체크 포인트:

- 성공 경로는 commit과 notifier 호출을 남긴다.
- 실패 경로는 rollback 상태만 남기고 notifier 호출을 생략한다.
- DB 없이도 use case branching을 빠르게 검증할 수 있다.

### `tests/test_pydantic_settings_patterns.py`

무엇을 보여주나:

- `monkeypatch.setenv()`
- `tmp_path`
- `_env_file`
- `_secrets_dir`

실행:

```bash
uv run pytest tests/test_pydantic_settings_patterns.py
```

체크 포인트:

- 실제 환경 변수가 `.env`보다 우선한다.
- secret dir가 env 부재 시 fallback source가 된다.

## 문서와 같이 읽기

- FastAPI 예제와 같이 읽기: `/fastapi/project-structure`, `/fastapi/dependency-injection`, `/playbooks/api-service-template`
- ASGI/Uvicorn 예제와 같이 읽기: `/intro/web-gateway-evolution`, `/fastapi/asgi-and-uvicorn`, `/fastapi/background-tasks-and-offloading`
- Realtime/운영 예제와 같이 읽기: `/fastapi/websockets-streaming-and-middleware`, `/fastapi/proxy-health-and-shutdown`
- WebSocket 실전 패턴과 같이 읽기: `/fastapi/websocket-practical-patterns`
- SQLAlchemy 예제와 같이 읽기: `/sqlalchemy/session-and-unit-of-work`, `/sqlalchemy/relationships-and-loading`
- Pydantic 예제와 같이 읽기: `/pydantic/core-schema`, `/pydantic/validation-pipeline`
- Asyncio 예제와 같이 읽기: `/asyncio/cancellation-and-taskgroup`, `/asyncio/queues-and-backpressure`
- Dataclass 예제와 같이 읽기: `/pythonic/dataclasses`
- 메타프로그래밍 예제와 같이 읽기: `/pythonic/metaprogramming-advanced`
- CPython 실험 예제와 같이 읽기: `/runtime/cpython-internals-advanced`
- Testing 예제와 같이 읽기: `/fastapi/lifespan-and-testing`, `/playbooks/testing-with-pytest-fixtures`
