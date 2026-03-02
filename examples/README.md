# Examples

이 디렉터리는 핸드북 문서를 "읽고 끝내는 것"이 아니라 바로 실행해보며 감을 잡도록 만든 예제 모음이다. 예제는 크게 두 축으로 나뉜다.

- 버전별 변화 예제: Python 3.10~3.14에서 새로 들어온 기능을 빠르게 체감
- 주제별 심화 예제: Pydantic, asyncio, FastAPI, SQLAlchemy 같은 실전 주제를 코드로 확인

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
| Pythonic | `py310_pattern_matching.py` | Python 문법이 데이터 shape와 제어 흐름을 얼마나 자연스럽게 표현하는지 바로 체감 |
| Typing | `py310_typing_and_zip_strict.py`, `py312_type_params.py` | modern typing 문법과 boundary 설계 감각을 같이 잡기 좋음 |
| Runtime | `py312_sys_monitoring.py`, `py313_runtime_modes.py`, `py314_interpreter_pool.py` | CPython 런타임이 어떤 방향으로 진화하는지 보여줌 |
| Asyncio | `py311_exception_groups_and_taskgroup.py`, `asyncio_backpressure_and_cancellation.py` | 구조적 동시성, cancellation, backpressure를 함께 익히기 좋음 |
| Pydantic | `pydantic_validation_pipeline.py` | core schema, strict/lax, validator/serializer 흐름을 한 번에 보여줌 |
| FastAPI / SQLAlchemy | `fastapi_service_template_example.py`, `sqlalchemy_loading_strategies.py` | 서비스 경계와 ORM 로딩 전략을 바로 실행해볼 수 있음 |

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

## 문서와 같이 읽기

- FastAPI 예제와 같이 읽기: `/fastapi/project-structure`, `/fastapi/dependency-injection`, `/playbooks/api-service-template`
- SQLAlchemy 예제와 같이 읽기: `/sqlalchemy/session-and-unit-of-work`, `/sqlalchemy/relationships-and-loading`
- Pydantic 예제와 같이 읽기: `/pydantic/core-schema`, `/pydantic/validation-pipeline`
- Asyncio 예제와 같이 읽기: `/asyncio/cancellation-and-taskgroup`, `/asyncio/queues-and-backpressure`
