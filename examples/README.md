# Examples

이 디렉터리는 "Python 3.10~3.14에서 무엇이 바뀌었는지"를 코드로 바로 확인하는 학습용 예제 모음이다.

각 파일은 다음 기준으로 만들었다.

- 어떤 기능이 추가되었는지
- 왜 그 기능이 필요해졌는지
- 실무에서 언제 쓰면 좋은지
- 실행하면 어떤 지점을 눈여겨봐야 하는지

모든 예제는 이 저장소의 `.venv`에 있는 Python 3.14.3 기준으로 점검했다.

## 먼저 알아둘 점

- 예제는 "도입 버전" 기준으로 분류했지만, 실제 실행은 Python 3.14.3에서 한다.
- 그래서 3.10 기능 예제도 3.14 인터프리터에서 돌린다.
- 일부 문법은 도입 버전보다 낮은 인터프리터에서는 파싱 자체가 되지 않는다.
  - 예: `class Box[T]`, `type Row[T] = ...`, `t"..."`, `InterpreterPoolExecutor`

## 추천 학습 순서

처음 다시 감을 잡는다면 아래 순서가 가장 효율적이다.

1. 3.10 문법 생산성: `match`, `TypeGuard`, `ParamSpec`, `zip(strict=True)`
2. 3.11 동시성과 실패 모델: `TaskGroup`, `ExceptionGroup`, `except*`
3. 3.12 타입 문법 현대화: 타입 파라미터 문법, `type` 별칭, `sys.monitoring`
4. 3.13 런타임 방향성: free-threaded, JIT, 타입 기본값, `warnings.deprecated`
5. 3.14 메타프로그래밍/병렬성: `annotationlib`, t-string, subinterpreter executor

## 실행 방법

개별 파일 실행:

```bash
./.venv/bin/python examples/py310_pattern_matching.py
./.venv/bin/python examples/py311_exception_groups_and_taskgroup.py
./.venv/bin/python examples/py314_template_strings.py
```

전체 예제 순회:

```bash
for file in examples/*.py; do
  echo "=== $file ==="
  ./.venv/bin/python "$file"
done
```

타입 체크와 린트:

```bash
uv run ty check
uv run ruff check .
```

## 버전별 예제 맵

| 버전 | 파일 | 핵심 기능 | 이 예제를 보는 이유 |
| --- | --- | --- | --- |
| 3.10 | `py310_pattern_matching.py` | `match/case` | 데이터 모양으로 분기하는 코드를 얼마나 짧게 만들 수 있는지 체감 |
| 3.10 | `py310_typing_and_zip_strict.py` | `ParamSpec`, `TypeGuard`, `zip(strict=True)` | "정교한 타입"과 "조용한 버그 방지"가 함께 어떻게 바뀌는지 확인 |
| 3.11 | `py311_exception_groups_and_taskgroup.py` | `ExceptionGroup`, `except*`, `TaskGroup` | 비동기 실패를 하나의 예외로 뭉개지 않고 보존하는 모델 이해 |
| 3.11 | `py311_tomllib.py` | `tomllib` | `pyproject.toml` 시대의 기본 설정 파서 확인 |
| 3.12 | `py312_type_params.py` | 새 제네릭 문법, `type` 별칭 | `TypeVar`/`Generic` 보일러플레이트가 얼마나 줄었는지 확인 |
| 3.12 | `py312_sys_monitoring.py` | `sys.monitoring` | 디버거/프로파일러가 저비용 이벤트를 어떻게 받는지 감 잡기 |
| 3.13 | `py313_runtime_modes.py` | free-threaded/JIT 상태 조회 | CPython 런타임이 어디로 가는지 방향성 이해 |
| 3.13 | `py313_type_defaults_and_deprecated.py` | 타입 파라미터 기본값, `warnings.deprecated`, `locals()` 의미 | 제네릭 API 사용성, deprecation 신호, locals 동작 이해 |
| 3.14 | `py314_annotationlib.py` | `annotationlib`, 지연 평가 어노테이션 | 프레임워크가 어노테이션을 읽는 방식이 왜 바뀌는지 확인 |
| 3.14 | `py314_template_strings.py` | `t"..."`, `string.templatelib` | 문자열 결과가 아니라 보간 구조 자체를 다루는 법 이해 |
| 3.14 | `py314_interpreter_pool.py` | `InterpreterPoolExecutor` | thread/process 사이의 새로운 병렬 실행 선택지 이해 |

## 주제별 심화 예제

버전별 변화 외에, 핸드북의 핵심 주제를 직접 만져볼 수 있는 심화 예제도 추가했다.

| 주제 | 파일 | 핵심 포인트 | 이 예제를 보는 이유 |
| --- | --- | --- | --- |
| Pydantic v2 | `pydantic_validation_pipeline.py` | `TypeAdapter`, strict vs lax, validator, serializer | Pydantic을 BaseModel 사용법이 아니라 validation pipeline 관점으로 이해 |
| Asyncio | `asyncio_backpressure_and_cancellation.py` | `TaskGroup`, bounded queue, `Semaphore`, `Queue.shutdown()`, timeout | 구조적 동시성과 backpressure가 실제로 어떻게 엮이는지 확인 |

### `pydantic_validation_pipeline.py`

무엇을 보여주나:

- `TypeAdapter`와 `BaseModel`이 같은 엔진을 공유한다는 점
- `AfterValidator`로 재사용 가능한 타입 규칙 만들기
- strict Python input과 strict JSON input의 차이
- `field_validator`와 `field_serializer`의 역할 분리

왜 중요하나:

- Pydantic을 DTO 선언 도구로만 이해하면 `TypeAdapter`, strict mode, serializer 설계를 놓치기 쉽다.
- FastAPI, settings, ingestion pipeline에서는 "입력 규칙"과 "출력 규칙"이 다르다는 감각이 매우 중요하다.

언제 쓰면 좋나:

- request/response DTO 설계
- queue/event payload 검증
- 모델 클래스 없이 임의 타입 구조를 빠르게 검증할 때

실행 시 체크 포인트:

- `adapter.core_schema["type"]`가 `list`로 출력되는지 본다.
- `"7"` 같은 문자열 입력이 어떻게 정수/날짜로 변환되는지 본다.
- strict Python input은 실패하고, strict JSON input은 성공하는 date 예제를 확인한다.

실행:

```bash
./.venv/bin/python examples/pydantic_validation_pipeline.py
```

### `asyncio_backpressure_and_cancellation.py`

무엇을 보여주나:

- `TaskGroup` 기반 worker pool
- `Queue(maxsize=2)`로 producer 속도 제한
- `Semaphore`로 downstream 동시성 제한
- `queue.join()` + `Queue.shutdown()` 기반 종료
- `asyncio.timeout()`으로 전체 작업 상한 걸기

왜 중요하나:

- 실무 async 코드는 단순 fan-out보다 shutdown과 overload 제어가 더 자주 문제를 만든다.
- bounded queue와 semaphore가 없으면 메모리와 downstream API가 먼저 터진다.

언제 쓰면 좋나:

- background worker
- webhook/event 처리 파이프라인
- 외부 API fan-out 작업

실행 시 체크 포인트:

- queue가 꽉 차면 producer가 자연스럽게 느려지는지 본다.
- worker는 semaphore 덕분에 동시에 2개까지만 처리한다.
- 모든 작업이 끝나면 `shutdown` 로그와 함께 task가 깔끔하게 끝나는지 본다.

실행:

```bash
./.venv/bin/python examples/asyncio_backpressure_and_cancellation.py
```

## 3.10

### `py310_pattern_matching.py`

무엇을 보여주나:

- 매핑 패턴
- 시퀀스 패턴
- 클래스 패턴
- OR 패턴과 가드

왜 중요하나:

- Python 3.9 이전에는 이런 코드를 `if/elif`, `isinstance`, 인덱싱, 키 존재 여부 검사로 길게 써야 했다.
- 이벤트 디스패치나 AST 해석 같은 코드가 훨씬 읽기 쉬워진다.

언제 쓰면 좋나:

- JSON payload 라우팅
- 명령 메시지 파싱
- 토큰/AST 노드 처리
- 상태 머신 분기

실행 시 체크 포인트:

- dict 입력은 매핑 패턴으로 매칭된다.
- list 입력은 `head`, `tail`로 분해된다.
- `Point` 객체는 클래스 패턴으로 풀린다.
- `int() | float()` OR 패턴과 가드가 같이 동작한다.

실행:

```bash
./.venv/bin/python examples/py310_pattern_matching.py
```

### `py310_typing_and_zip_strict.py`

무엇을 보여주나:

- `ParamSpec`으로 데코레이터 시그니처 보존
- `TypeGuard`로 런타임 검사 결과를 타입 좁히기에 연결
- `zip(strict=True)`로 길이 불일치 즉시 실패

왜 중요하나:

- 3.10 이전에는 데코레이터를 정확히 타입 지정하기가 불편했다.
- 사용자 정의 predicate가 타입 체커와 연결되지 않아 narrowing이 거칠었다.
- `zip()`은 길이 차이를 조용히 잘라먹어서 데이터 손실 버그를 만들기 쉬웠다.

언제 쓰면 좋나:

- 로깅/트레이싱/캐싱 데코레이터
- 리스트 필터링 후 타입 안전한 후속 처리
- 두 시퀀스가 반드시 1:1 대응해야 하는 데이터 처리

실행 시 체크 포인트:

- `@traced`가 붙은 `add()` 호출이 정상 동작한다.
- `is_str_list()`가 참이면 `values`가 `list[str]`처럼 다뤄진다.
- `zip(strict=True)`는 길이 차이가 있으면 실패해야 한다는 의도를 명확히 만든다.

실행:

```bash
./.venv/bin/python examples/py310_typing_and_zip_strict.py
```

## 3.11

### `py311_exception_groups_and_taskgroup.py`

무엇을 보여주나:

- `asyncio.TaskGroup`
- `ExceptionGroup`
- `except*`

왜 중요하나:

- 비동기 작업 여러 개를 동시에 돌리면 실패도 여러 개일 수 있다.
- 예전에는 첫 예외만 보거나, 예외를 임의로 뭉개기 쉬웠다.
- 3.11부터는 구조적 동시성과 구조적 예외 처리가 같이 들어왔다.

언제 쓰면 좋나:

- 여러 API를 병렬 호출하는 로직
- fan-out/fan-in 데이터 수집기
- 병렬 배치 작업

실행 시 체크 포인트:

- `TaskGroup` 안에서 두 작업이 같이 시작된다.
- 예외는 하나로 평평해지지 않고 그룹으로 유지된다.
- `except* ValueError`, `except* TypeError`가 같은 그룹에서 타입별로 나눠 잡는다.

실행:

```bash
./.venv/bin/python examples/py311_exception_groups_and_taskgroup.py
```

### `py311_tomllib.py`

무엇을 보여주나:

- 표준 라이브러리로 TOML 문자열 파싱
- `pyproject.toml` 스타일 구조를 dict로 읽기

왜 중요하나:

- Python 패키징과 툴 설정의 중심이 TOML로 이동했다.
- `tomllib` 덕분에 단순 읽기 목적이라면 외부 TOML 의존성을 줄일 수 있다.

언제 쓰면 좋나:

- 프로젝트 설정 읽기
- 학습용 설정 파서 만들기
- 배포 스크립트/도구에서 TOML 소비

실행 시 체크 포인트:

- `[project]`, `[tool.study]` 섹션이 중첩 dict로 파싱된다.
- 리스트와 정수 값이 각각 적절한 Python 타입으로 들어온다.

실행:

```bash
./.venv/bin/python examples/py311_tomllib.py
```

## 3.12

### `py312_type_params.py`

무엇을 보여주나:

- `type Row[T] = ...`
- `class Box[T]`
- `def first[T](...)`
- `__type_params__`

왜 중요하나:

- 3.12는 typing을 "라이브러리 규약"에서 "언어 문법" 쪽으로 끌고 왔다.
- 제네릭 선언이 훨씬 짧고 읽기 쉬워졌다.

언제 쓰면 좋나:

- 컬렉션 래퍼
- 타입 안정성이 중요한 헬퍼 함수
- 라이브러리 API 설계

실행 시 체크 포인트:

- `Box("python")`처럼 타입 인자가 추론되는 느낌을 본다.
- `Row[int]`가 일반 alias처럼 읽히는지 본다.
- `__type_params__`를 출력해 컴파일러가 저장한 타입 파라미터 메타데이터를 확인한다.

실행:

```bash
./.venv/bin/python examples/py312_type_params.py
```

### `py312_sys_monitoring.py`

무엇을 보여주나:

- `sys.monitoring.use_tool_id`
- 이벤트 콜백 등록
- 특정 이벤트만 활성화

왜 중요하나:

- 기존 `sys.settrace()` 기반 접근은 항상 비쌌다.
- 3.12는 디버거, 프로파일러, 커버리지 도구를 위한 더 저비용 API를 제공한다.

언제 쓰면 좋나:

- 커스텀 프로파일러/디버거 실험
- 코드 커버리지 도구 학습
- 인터프리터 이벤트를 직접 보고 싶은 내부 동작 공부

실행 시 체크 포인트:

- `sample_work()` 안에서만 line 이벤트가 출력된다.
- 모든 이벤트를 켜는 것이 아니라 필요한 이벤트만 선택한다.
- 마지막에 monitoring slot을 반드시 정리한다.

실행:

```bash
./.venv/bin/python examples/py312_sys_monitoring.py
```

## 3.13

### `py313_runtime_modes.py`

무엇을 보여주나:

- 현재 프로세스에서 GIL이 활성화되어 있는지
- 현재 빌드가 JIT를 지원하는지
- JIT가 현재 프로세스에서 실제 활성화되어 있는지

왜 중요하나:

- 3.13은 "지금 당장 생산성 기능"보다 "CPython이 앞으로 어디로 가는가"를 보여주는 버전이다.
- free-threaded와 JIT는 둘 다 런타임 진화 방향을 이해하는 데 핵심이다.

언제 쓰면 좋나:

- 벤치마크 실험
- CI 환경 진단
- 서로 다른 Python 빌드 비교

실행 시 체크 포인트:

- `available`과 `enabled`는 의미가 다르다.
- GIL 여부와 JIT 여부는 빌드/실행 옵션에 따라 달라질 수 있다.

실행:

```bash
./.venv/bin/python examples/py313_runtime_modes.py
```

### `py313_type_defaults_and_deprecated.py`

무엇을 보여주나:

- 제네릭 타입 기본값
- `warnings.deprecated`
- 함수 내부 `locals()`의 동작 감각

왜 중요하나:

- 타입 기본값은 generic API 사용성을 올려준다.
- deprecation은 런타임 경고와 정적 도구 신호를 함께 주는 방향으로 바뀌고 있다.
- `locals()`는 예전부터 직관과 다른 지점이 많았고, 3.13은 그 의미를 더 명확하게 정리했다.

언제 쓰면 좋나:

- "대부분 이 타입을 쓰되, 필요하면 바꿔라" 같은 generic API
- 이전 API를 단계적으로 폐기하는 라이브러리
- 디버깅/메타프로그래밍 시 locals 동작 확인

실행 시 체크 포인트:

- `Cache[int]`가 사실상 `Cache[int, str]`로 동작한다.
- deprecated 함수 호출 시 경고가 발생한다.
- `locals()` 매핑을 바꿔도 실제 로컬 변수 `value`는 그대로 남는다.

실행:

```bash
./.venv/bin/python examples/py313_type_defaults_and_deprecated.py
```

## 3.14

### `py314_annotationlib.py`

무엇을 보여주나:

- `annotationlib.get_annotations`
- `Format.STRING`
- forward reference를 다루는 방식

왜 중요하나:

- 어노테이션은 타입 힌트만이 아니라 프레임워크 메타데이터로도 많이 쓰인다.
- 3.14는 어노테이션을 "언제 평가할지"를 더 유연하게 다룰 수 있게 만들었다.

언제 쓰면 좋나:

- DI 프레임워크
- 데이터 검증/직렬화 프레임워크
- 어노테이션 기반 라우팅/등록 로직

실행 시 체크 포인트:

- 문자열 포맷으로 보면 `Later`가 원본 표현처럼 남는다.
- 평가된 어노테이션을 보면 실제 클래스 객체로 해석된다.

실행:

```bash
./.venv/bin/python examples/py314_annotationlib.py
```

### `py314_template_strings.py`

무엇을 보여주나:

- `t"..."`가 `str`이 아니라 `Template`을 만든다는 점
- 보간식의 원본 표현식과 계산 결과를 동시에 보존한다는 점

왜 중요하나:

- `f-string`은 즉시 문자열이 되기 때문에 템플릿 엔진 입장에서는 정보가 사라진다.
- t-string은 "보간 구조 자체"를 객체로 유지해서 후처리할 수 있게 해준다.

언제 쓰면 좋나:

- 로깅 이벤트 구조화
- 국제화/i18n
- 안전한 렌더링 계층
- 템플릿/코드 생성기

실행 시 체크 포인트:

- `type(template)`가 `Template`인지 확인한다.
- `strings`, `values`, `interpolations`가 각각 무엇을 담는지 본다.
- 각 interpolation에 원래 표현식 문자열이 보존되는지 확인한다.

실행:

```bash
./.venv/bin/python examples/py314_template_strings.py
```

### `py314_interpreter_pool.py`

무엇을 보여주나:

- `InterpreterPoolExecutor`
- 서브인터프리터 기반 작업 분배

왜 중요하나:

- Python 병렬성은 오랫동안 thread vs process 중심으로 설명됐다.
- 3.14는 같은 프로세스 안에서 더 강한 격리를 가진 실행 단위를 표준 라이브러리 레벨에서 다루기 쉽게 만들었다.

언제 쓰면 좋나:

- 상태 공유가 적은 CPU 작업 실험
- subinterpreter 모델 학습
- thread/process 사이 trade-off 비교

실행 시 체크 포인트:

- executor 사용법은 `ProcessPoolExecutor`와 비슷해 보인다.
- 하지만 worker는 thread가 아니라 별도 interpreter다.
- "메모리를 편하게 공유"하는 모델이 아니라는 점을 같이 기억한다.

실행:

```bash
./.venv/bin/python examples/py314_interpreter_pool.py
```

## 이 README를 어떻게 활용하면 좋은가

가장 추천하는 방식은 다음 순서다.

1. 먼저 `docs/python-3.10-3.14-deep-dive.md`를 읽고 큰 흐름을 잡는다.
2. 이 `examples/README.md`에서 오늘 볼 예제를 하나 고른다.
3. 해당 `.py` 파일 상단 주석에서 `무엇 / 왜 / 언제`를 먼저 읽는다.
4. 예제를 실행해서 출력이 왜 그렇게 나오는지 확인한다.
5. 코드를 조금 바꿔보며 경계 사례를 직접 실험한다.

추천 실험:

- pattern matching에 새 `case`를 추가해보기
- `zip(strict=True)`의 길이를 일부러 다르게 만들어보기
- `TaskGroup` 안 task를 하나 더 늘려보기
- `sys.monitoring.events`를 다른 이벤트로 바꿔보기
- `Template`에 더 복잡한 표현식을 넣어보기

## 관련 문서

- 상위 설명: `../docs/python-3.10-3.14-deep-dive.md`
- 런타임 비교: `../docs/cpython-vs-go-runtime.md`
