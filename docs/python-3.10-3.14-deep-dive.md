# Python 3.10~3.14 Deep Dive

이 문서는 "Python 3.9 이후 감이 떨어진 상태에서 3.10~3.14를 한 번에 따라잡기"를 목표로 정리했다. 기준 구현체는 CPython이고, 예제는 이 저장소의 Python 3.14.3 환경에서 확인했다.

## 이 문서를 읽는 법

이 문서는 처음부터 끝까지 정독해도 되지만, 아래처럼 읽는 편이 훨씬 효율적이다.

- 빠르게 감만 잡고 싶다:
  - `3분 요약` -> `3.9에서 3.14로 바뀐 감각` -> `지금 바로 체감이 큰 것`
- 실무 우선으로 보고 싶다:
  - 3.10 -> 3.11 -> 3.12 순으로 본다.
- 타입 시스템 변화가 궁금하다:
  - 3.10 `ParamSpec`, `TypeGuard`
  - 3.12 타입 파라미터 문법
  - 3.13 타입 파라미터 기본값
  - 3.14 지연 평가 어노테이션
- 런타임/내부 동작이 궁금하다:
  - 3.11 적응형 특수화
  - 3.12 `sys.monitoring`
  - 3.13 free-threaded/JIT
  - 3.14 subinterpreter, incremental GC

## 3분 요약

3.10~3.14는 한 줄로 요약하면 이렇다.

- 3.10: "코드가 더 읽기 좋아진 버전"
- 3.11: "예외 모델과 실행기 성능이 확 달라진 버전"
- 3.12: "typing이 드디어 언어 문법처럼 느껴지기 시작한 버전"
- 3.13: "GIL 이후의 CPython을 시험하기 시작한 버전"
- 3.14: "프레임워크/도구 제작자에게 중요한 메타프로그래밍 API가 열린 버전"

버전별로 한 번에 보면:

| 버전 | 한 줄 요약 | 가장 먼저 기억할 것 | 대표 예제 |
| --- | --- | --- | --- |
| 3.10 | 오래된 분기/typing 불편함을 강하게 정리 | `match`, `X | Y`, `zip(strict=True)` | `examples/py310_pattern_matching.py` |
| 3.11 | 속도와 구조적 예외 처리가 크게 바뀜 | PEP 659, `ExceptionGroup`, `TaskGroup` | `examples/py311_exception_groups_and_taskgroup.py` |
| 3.12 | 타입 문법이 현대화되고 도구 API가 열림 | PEP 695, PEP 701, PEP 709, `sys.monitoring` | `examples/py312_type_params.py` |
| 3.13 | free-threaded/JIT 등 런타임 실험이 표면화 | PEP 703, PEP 744, PEP 667 | `examples/py313_runtime_modes.py` |
| 3.14 | 어노테이션/템플릿/인터프리터가 실사용 단계로 진입 | PEP 649/749, PEP 734, PEP 750 | `examples/py314_annotationlib.py` |

## 변화의 큰 흐름

3.10~3.14는 단순 문법 추가 구간이 아니다. 이 시기에는 아래 다섯 축이 동시에 움직였다.

| 축 | 3.9 이전 느낌 | 3.10~3.14에서 바뀐 방향 |
| --- | --- | --- |
| 언어 표현력 | `if/elif`, 장황한 typing, 즉시 문자열화 | `match`, `X | Y`, 새 제네릭 문법, t-string |
| 런타임 성능 | 느리지만 단순한 인터프리터 이미지 | 3.11 적응형 특수화, 3.12 comprehension 개선, 3.13 JIT 실험 |
| 동시성 모델 | `threading` vs `multiprocessing`, 예외는 1개 중심 | `TaskGroup`, `ExceptionGroup`, subinterpreter, free-threaded 실험 |
| 타입 시스템 | `TypeVar`, `Generic`, 긴 `Union[...]` | 타입 파라미터 문법, 기본값, 지연 평가 어노테이션 |
| 도구/메타프로그래밍 | `sys.settrace`, 문자열 forward ref, 별도 TOML 파서 | `sys.monitoring`, `annotationlib`, `tomllib` |

## 3.9에서 3.14로 바뀐 감각

이 시기를 공부할 때는 "기능 목록"보다 "머릿속 모델이 어떻게 바뀌는지"를 보는 편이 좋다.

| 주제 | 3.9 감각 | 3.14 감각 |
| --- | --- | --- |
| 분기 | 값 비교와 타입 검사를 손으로 길게 푼다 | 데이터 형태 자체를 패턴으로 매칭한다 |
| 타입 힌트 | 주석 같은 보조 정보에 가깝다 | API 계약과 도구 연동의 중심으로 간다 |
| 비동기 실패 | 첫 예외 위주로 본다 | 여러 실패를 구조적으로 보존한다 |
| 성능 | "Python은 원래 느리다"로 뭉뚱그리기 쉽다 | 인터프리터 특수화, JIT, GC 개선까지 세분화해 본다 |
| 병렬성 | 스레드는 GIL 때문에 한계, CPU는 프로세스 | free-threaded와 subinterpreter까지 선택지가 늘어난다 |
| 어노테이션 | 평가 시점과 forward reference가 자주 골칫거리 | 필요한 포맷으로 안전하게 읽어오는 방향으로 간다 |

## 버전별 Deep Dive

---

## Python 3.10

### 핵심 한 줄

3.10은 "Python 코드가 더 선언적으로 읽히기 시작한 버전"이다.

### 먼저 기억할 3가지

1. `match/case`는 `switch`보다 훨씬 강한 구조 분해 도구다.
2. `X | Y`, `ParamSpec`, `TypeGuard` 덕분에 typing이 덜 고통스러워졌다.
3. `zip(strict=True)`는 작지만 실무 버그를 줄이는 좋은 변화다.

### 기능 지도

| 기능 | 왜 들어왔나 | 언제 체감되나 |
| --- | --- | --- |
| Structural Pattern Matching | shape-based branching을 짧고 읽기 좋게 만들기 위해 | 이벤트 디스패치, 파서, 상태 머신 |
| `X | Y` 유니언 | `Union[X, Y]` 문법을 덜 장황하게 만들기 위해 | 함수 시그니처, 데이터 모델 |
| `ParamSpec` | 데코레이터가 원래 함수 시그니처를 보존하도록 하기 위해 | 로깅/캐싱/트레이싱 데코레이터 |
| `TypeGuard` | 런타임 검사와 정적 타입 좁히기를 연결하기 위해 | predicate 함수, validation code |
| `zip(strict=True)` | 길이 불일치를 조용히 삼키는 버그를 줄이기 위해 | ETL, 동기화된 리스트 처리 |

### 1. Structural Pattern Matching

핵심 기능은 `match ... case ...`다. 표면적으로는 다른 언어의 `switch`처럼 보이지만 실제로는 더 강력하다.

- 값 비교만 하는 문법이 아니다.
- 시퀀스 분해, 매핑 키 매칭, 클래스 패턴, 가드(`if`)를 지원한다.
- 성공하면 새 이름을 바인딩한다.

왜 들어왔나:

- Python은 데이터 분해를 위해 `if/elif`, `isinstance`, 인덱싱, 키 검사 코드를 길게 늘어놓는 경우가 많았다.
- JSON 이벤트, AST, 토큰, 명령 메시지처럼 "형태를 보고 분기"하는 코드를 훨씬 읽기 좋게 만들려는 목적이었다.

어떻게 동작하나:

- 컴파일러가 패턴을 보고 분기 트리를 만든다.
- 런타임은 리터럴 비교, 시퀀스/매핑 모양 확인, 클래스 패턴의 경우 `__match_args__` 등을 이용해 매칭한다.
- 표현식이 아니라 제어문이므로 `match` 자체가 값을 돌려주지는 않는다.

언제 특히 좋나:

- 이벤트 디스패치
- 파서 구현
- 도메인 상태 머신
- API payload 라우팅

주의할 점:

- 단순 enum 분기만 있을 때는 `if/elif`가 더 읽기 좋을 수도 있다.
- 패턴을 과하게 중첩하면 오히려 이해가 어려워질 수 있다.

예제:

- `examples/py310_pattern_matching.py`

### 2. typing ergonomics 개선

3.10은 "typing이 현실 코드에 덜 거슬리게" 만든 버전이다.

- `X | Y` 유니언 표기(PEP 604)
- `ParamSpec`(PEP 612): 데코레이터처럼 "호출 시그니처를 전달"하는 타입 모델
- 명시적 타입 별칭(PEP 613)
- `TypeGuard`(PEP 647): 런타임 검사 결과를 정적 타입 좁히기에 연결

왜 중요하나:

- 3.9 이전 typing은 `Union[X, Y]`, `Callable[..., T]` 같은 표기가 길고, 데코레이터 정확도가 떨어졌다.
- 3.10부터는 타입 힌트가 "코드를 설명하는 주석" 수준을 넘어 실제 API 설계 도구가 된다.

어떻게 체감되나:

- 데코레이터가 원래 함수의 인자 타입을 그대로 전달할 수 있다.
- 사용자 정의 predicate가 타입 체커에게 실제 narrowing 신호를 준다.

실무 포인트:

- 팀이 typing을 적극적으로 쓰는 회사라면 3.10은 사실상 첫 번째 "현대 typing" 버전으로 봐도 된다.

예제:

- `examples/py310_typing_and_zip_strict.py`

### 3. 작지만 실전에서 중요한 변화

- `zip(strict=True)`(PEP 618): 서로 길이가 다른 입력을 조용히 잘라먹지 않고 즉시 실패시킨다.
- 디버거/프로파일러용 정확한 라인 정보(PEP 626): 트레이싱 도구 정확도를 높였다.
- 에러 메시지가 더 구체적으로 바뀌기 시작했다.

한 줄 정리:

- 3.10은 화려한 문법 버전처럼 보이지만, 실제로는 "코드 의도를 더 정확히 드러내는 버전"이다.

---

## Python 3.11

### 핵심 한 줄

3.11은 "성능과 비동기 예외 처리 모델이 같이 업그레이드된 버전"이다.

### 먼저 기억할 3가지

1. Faster CPython은 체감 성능에 꽤 의미 있는 변화를 만들었다.
2. `ExceptionGroup`과 `except*`는 async 시대의 예외 모델이다.
3. `TaskGroup`은 `asyncio`에 구조적 동시성 감각을 넣었다.

### 기능 지도

| 기능 | 왜 들어왔나 | 언제 체감되나 |
| --- | --- | --- |
| 적응형 특수화 인터프리터 | Python hot path 오버헤드를 줄이기 위해 | 속성 접근, 호출, 루프 |
| `ExceptionGroup` / `except*` | 여러 동시 실패를 보존하기 위해 | fan-out async, 병렬 배치 |
| `asyncio.TaskGroup` | task 생명주기를 블록 단위로 묶기 위해 | 서비스 백엔드, 비동기 수집기 |
| `tomllib` | `pyproject.toml` 시대의 기본 파서 제공 | 설정 파싱, 툴 구현 |
| 더 정밀한 traceback | 디버깅 효율을 높이기 위해 | 복잡한 표현식 디버깅 |

### 1. Faster CPython: 적응형 특수화 인터프리터

3.11의 가장 큰 변화는 속도다. 핵심 아이디어는 "바이트코드는 유지하되, 자주 보는 패턴을 실행 중에 특수화"하는 것이다.

왜 들어왔나:

- Python의 강점은 생산성이지만, 순수 Python 루프와 속성 접근은 오버헤드가 컸다.
- JIT를 즉시 기본 탑재하기보다, 인터프리터 자체를 더 똑똑하게 만드는 접근을 먼저 택했다.

어떻게 동작하나:

- 처음에는 일반적인 opcode로 실행한다.
- 실행 중 타입/패턴이 안정적으로 반복되면 opcode를 더 구체적인 전용 형태로 바꾼다.
- 속성 접근, 전역 조회, 함수 호출 같은 hot path가 빨라진다.

중요한 점:

- Python이 갑자기 "정적 컴파일 언어"처럼 되는 것은 아니다.
- 하지만 많은 현실 코드에서 "아무것도 안 바꿨는데 체감 속도"가 좋아진 버전이 3.11이다.

### 2. ExceptionGroup + `except*`

비동기/병렬 작업에서는 실패가 하나가 아니라 여러 개일 수 있다. 기존 `except` 모델은 이 상황을 다루기 불편했다.

왜 들어왔나:

- 여러 task를 동시에 돌릴 때 `ValueError`와 `TypeError`가 같이 발생할 수 있다.
- 기존 모델은 첫 예외만 전파하거나, 나머지 예외를 잃어버리기 쉬웠다.

어떻게 동작하나:

- `ExceptionGroup`은 예외 묶음을 표현한다.
- `except* ValueError`는 그룹 전체가 아니라 "그 안의 ValueError 부분집합"만 꺼내 처리한다.
- 처리되지 않은 나머지 예외는 다시 그룹 형태로 남는다.

왜 실무에서 중요한가:

- 실패를 버리지 않는다.
- 어떤 task가 어떤 이유로 실패했는지 보존된다.
- 분산 호출, 병렬 수집, 배치 처리 코드에서 디버깅 품질이 올라간다.

예제:

- `examples/py311_exception_groups_and_taskgroup.py`

### 3. `asyncio.TaskGroup`

3.11부터 `asyncio`에도 구조적 동시성(structured concurrency) 감각이 들어왔다.

왜 중요하나:

- 예전에는 `create_task()`를 흩뿌리고 누가 취소/예외를 정리할지 개발자가 직접 관리하기 쉬웠다.
- `TaskGroup`은 task들의 생명주기를 블록 경계 안에 묶는다.

어떻게 동작하나:

- 그룹 안 task 하나가 실패하면 관련 task들을 취소한다.
- 종료 시점에 예외를 `ExceptionGroup`으로 묶어 보고한다.

이 조합이 중요한 이유:

- `TaskGroup`과 `ExceptionGroup`은 따로 배워도 되지만, 실무에서는 거의 같이 등장한다.

### 4. `tomllib`

왜 중요한가:

- Python 패키징 세계는 `pyproject.toml` 중심으로 이동했다.
- TOML 파서를 표준 라이브러리로 제공하면서 "설정 파싱의 기본 도구"가 하나 정리됐다.

예제:

- `examples/py311_tomllib.py`

### 5. 더 정밀한 에러 위치

3.11은 예외 위치와 traceback 품질도 좋아졌다. 특히 긴 표현식 안에서 어느 부분이 실패했는지 더 정확하게 가리킨다.

한 줄 정리:

- 3.11은 "Python이 느리고 async 에러가 답답하다"는 오래된 인식을 꽤 많이 바꾼 버전이다.

---

## Python 3.12

### 핵심 한 줄

3.12는 "typing이 라이브러리 문법이 아니라 Python 문법처럼 느껴지는 버전"이다.

### 먼저 기억할 3가지

1. `class Box[T]`, `def first[T]`, `type Row[T] = ...`는 3.12 이후 감각이다.
2. `sys.monitoring`은 툴 제작자에게 매우 큰 변화다.
3. 3.12는 3.13~3.14의 병렬성/런타임 변화로 이어지는 기반 버전이기도 하다.

### 기능 지도

| 기능 | 왜 들어왔나 | 언제 체감되나 |
| --- | --- | --- |
| 타입 파라미터 문법 | generics 보일러플레이트 제거 | 라이브러리 API 설계 |
| `type` 별칭 문법 | 타입 별칭을 더 선언적으로 표현 | 도메인 타입 모델링 |
| PEP 701 f-string 정식화 | 파서 일관성 확보 | 코드 생성, 복잡한 문자열 처리 |
| PEP 709 comprehension 개선 | 자주 쓰는 경로의 오버헤드 절감 | 리스트/딕트/셋 comprehension |
| `sys.monitoring` | tracing 도구의 고비용 문제 해결 | 디버거/프로파일러/커버리지 |

### 1. 타입 파라미터 문법과 `type` 별칭

3.12는 typing 역사에서 매우 큰 버전이다.

- `class Box[T]: ...`
- `def first[T](items: list[T]) -> T: ...`
- `type Row[T] = dict[str, T]`

왜 들어왔나:

- 기존 generics는 `TypeVar`, `Generic`, 별도 선언이 많아 진입 비용이 높았다.
- 타입 시스템을 언어 문법 수준으로 끌어올려 읽기/작성 비용을 줄이려는 목적이다.

어떻게 체감되나:

- 제네릭 선언이 함수/클래스 정의부에서 바로 보인다.
- API 설계가 더 선언적으로 읽힌다.
- 타입 문법이 "추가 라이브러리"가 아니라 언어 일부처럼 느껴진다.

예제:

- `examples/py312_type_params.py`

### 2. f-string 문법의 정식화

PEP 701은 "f-string을 예외 규칙 덩어리"에서 "정식 문법의 일부"로 끌어올렸다.

왜 중요하나:

- 예전에는 f-string 안에서 백슬래시, 중첩, 따옴표 처리 등에 이상한 제한이 있었다.
- 파서가 정식 문법으로 다루게 되면서 일관성이 좋아졌다.

실무 의미:

- 템플릿 문자열을 복잡하게 다루는 코드 생성기, SQL/DSL 조립, 디버그 출력에서 덜 깨진다.

### 3. comprehension inlining

왜 중요하나:

- 리스트/딕트/셋 comprehension은 Python 코드에서 아주 흔하다.
- 3.12는 이 경로의 오버헤드를 줄였다.

어떻게 이해하면 되나:

- comprehension이 별도의 작은 함수 프레임을 더 만드는 식의 비용을 줄여서 더 직접적으로 실행되게 했다.
- 아주 화려한 기능은 아니지만 "자주 쓰는 코드가 자연스럽게 빨라지는" 개선이다.

### 4. `sys.monitoring`

이건 툴링 관점에서 매우 중요하다.

왜 들어왔나:

- 디버거, 프로파일러, 커버리지 도구는 인터프리터 이벤트를 봐야 한다.
- 기존 `sys.settrace()` 계열은 오버헤드가 커서 상시 사용이 부담스러웠다.

어떻게 동작하나:

- 인터프리터가 line/call/return 등 이벤트를 더 저비용으로 노출한다.
- 도구가 필요한 이벤트만 선택적으로 켤 수 있다.

실무 포인트:

- APM, 코드 커버리지, 샘플러, 디버거를 만드는 사람에게는 큰 변화다.
- 일반 앱 개발자도 "Python이 observability를 언어 차원에서 더 신경 쓰기 시작했다"는 신호로 읽으면 된다.

예제:

- `examples/py312_sys_monitoring.py`

### 5. per-interpreter GIL 기반 마련

3.12는 "각 인터프리터가 자신의 GIL을 갖는 방향"을 위한 기반 작업이 들어간 버전이다. 곧바로 모든 코드가 병렬화되는 것은 아니지만, 이후 3.13 free-threaded와 3.14 interpreter API 노출로 이어지는 중요한 중간 단계다.

한 줄 정리:

- 3.12는 문법은 typing 쪽이, 내부는 병렬성 쪽이 중요하다.

---

## Python 3.13

### 핵심 한 줄

3.13은 "CPython이 앞으로 어디로 갈지"를 보여주는 버전이다.

### 먼저 기억할 3가지

1. free-threaded CPython은 역사적으로 매우 큰 변화다.
2. JIT는 아직 실험적이지만 방향성은 분명하다.
3. `locals()` 의미 정리, 타입 기본값, deprecation 신호 강화 같은 세부 변화도 중요하다.

### 기능 지도

| 기능 | 왜 들어왔나 | 언제 체감되나 |
| --- | --- | --- |
| free-threaded 빌드 | GIL 한계를 줄이기 위해 | CPU 병렬 실험, 런타임 연구 |
| 실험적 JIT | hot path 성능 향상 가능성 탐색 | 성능 실험 |
| `locals()` 의미 정리 | 스코프/프레임 의미를 더 일관되게 | 디버깅, 메타프로그래밍 |
| 타입 파라미터 기본값 | generic API 사용성 향상 | 라이브러리 타입 설계 |
| `warnings.deprecated` | 정적/런타임 deprecation 신호 통합 | 라이브러리 마이그레이션 |

### 1. free-threaded CPython 실험판

3.13의 역사적 의미는 여기에 있다. PEP 703 기반으로 GIL 없이 동작하는 빌드가 실험 단계로 들어왔다.

왜 큰 사건인가:

- CPython은 오랫동안 "스레드는 편하지만 CPU 병렬성은 제한적"이라는 특성이 있었다.
- 데이터 처리, AI 전처리, 서버 백엔드에서 이 한계는 매우 자주 문제였다.

주의할 점:

- 기본 빌드가 바로 GIL-less가 된 것은 아니다.
- C extension 호환성, 객체 모델, 성능 trade-off가 있어서 점진적으로 가고 있다.

어떻게 이해하면 좋나:

- Python 런타임이 이제 "싱글 GIL만 가능한 구조"에서 벗어나기 시작했다.
- 앞으로 라이브러리 생태계가 이 방향을 얼마나 따라오느냐가 중요하다.

### 2. 실험적 JIT

3.13은 JIT도 실험적으로 도입했다.

왜 바로 기대치를 높이면 안 되나:

- Python의 성능 문제는 단순히 "기계어로 바꾸면 끝"이 아니다.
- 동적 객체 모델, C extension, 디버깅, 안정성 문제가 함께 얽혀 있다.

실무 관점:

- 지금은 "학습해야 할 개념"이지 "바로 production 성능 카드"로 보기엔 이르다.
- 하지만 CPython이 인터프리터 특수화 이후 JIT 영역까지 탐색하기 시작했다는 점이 중요하다.

예제:

- `examples/py313_runtime_modes.py`

### 3. `locals()` 의미가 더 명확해짐

Python 함수 내부에서 `locals()`는 오래전부터 직관과 다른 순간이 있었다. 3.13은 최적화된 스코프에서 그 의미를 더 명확하게 정의했다.

왜 중요하나:

- 디버깅, 메타프로그래밍, 프레임 조작, 템플릿 엔진 같은 코드에서 애매함이 버그 원인이 되기 쉬웠다.

실무 포인트:

- `locals()`는 여전히 "로컬 변수 슬롯을 마음대로 수정하는 API"가 아니다.
- 스냅샷/매핑으로 이해하는 편이 안전하다.

### 4. 타입 파라미터 기본값

3.12가 제네릭 문법을 열었다면, 3.13은 거기에 기본값까지 붙였다.

왜 좋은가:

- 흔한 generic API에서 기본 타입을 제공해 사용성과 정밀도를 같이 얻을 수 있다.

예제:

- `examples/py313_type_defaults_and_deprecated.py`

### 5. `warnings.deprecated`

타입 체커와 런타임 경고를 한 방향으로 맞추기 위한 기반이다.

왜 중요한가:

- 예전에는 "런타임 경고"와 "정적 분석 경고"가 따로 놀기 쉬웠다.
- deprecation을 API 계약의 일부로 더 구조적으로 표현할 수 있다.

한 줄 정리:

- 3.13은 "지금 당장 다 쓰는 기능"보다 "앞으로 Python이 어떤 런타임이 될 것인가"를 읽는 버전이다.

---

## Python 3.14

### 핵심 한 줄

3.14는 "프레임워크, 도구, 병렬 실행 모델" 쪽에서 특히 중요한 버전이다.

### 먼저 기억할 3가지

1. 지연 평가 어노테이션은 프레임워크 작성자에게 매우 중요하다.
2. `t"..."`는 `f-string` 대체가 아니라 다른 계층의 도구다.
3. `InterpreterPoolExecutor`는 Python 병렬성 선택지를 넓힌다.

### 기능 지도

| 기능 | 왜 들어왔나 | 언제 체감되나 |
| --- | --- | --- |
| 지연 평가 어노테이션 | forward ref와 조기 평가 문제 해결 | 프레임워크, DI, ORM |
| `annotationlib` | 어노테이션을 원하는 포맷으로 읽기 위해 | 메타프로그래밍, 도구 제작 |
| template string | 보간 구조 자체를 보존하기 위해 | 템플릿, 로깅, i18n |
| `InterpreterPoolExecutor` | thread/process 사이 선택지 확장 | 병렬 실험, 상태 분리 |
| incremental cyclic GC | pause 부담 완화 | 지연 시간 민감한 워크로드 |

### 1. 지연 평가 어노테이션이 기본이 됨

3.14의 핵심 변화 중 하나다.

왜 들어왔나:

- 어노테이션은 점점 타입 체커뿐 아니라 프레임워크, 의존성 주입, ORM, 데이터 검증에도 쓰이고 있다.
- 그런데 정의 시점 즉시 평가 모델은 forward reference, import cycle, 비용 문제를 자주 만들었다.

무엇이 달라졌나:

- 3.14는 어노테이션을 곧바로 단순 문자열로 바꾸는 접근이 아니라, "필요할 때 평가할 수 있는 표현"으로 다룬다.
- `annotationlib`로 문자열 형태, 값 형태 등 원하는 포맷으로 꺼낼 수 있다.

왜 실무적으로 좋은가:

- 순방향 참조를 문자열 따옴표로 감싸는 습관이 줄어든다.
- 프레임워크 작성자가 어노테이션을 더 안전하고 유연하게 읽을 수 있다.

예제:

- `examples/py314_annotationlib.py`

### 2. template string (`t"..."`)

이건 `f-string`의 대체가 아니라 역할이 다르다.

왜 들어왔나:

- `f-string`은 바로 문자열을 만들어버린다.
- 그러나 템플릿 엔진, i18n, 안전한 렌더링, 코드 생성기에서는 "문자열 결과"보다 "보간 구조 자체"가 필요하다.

어떻게 다르나:

- `t"..."`는 즉시 `str`을 만들지 않고 `Template` 객체를 만든다.
- 각 보간식의 원본 표현식, 값, 변환 정보 등을 구조적으로 유지한다.

언제 쓰나:

- 로깅/렌더링 레이어를 직접 만들 때
- 안전한 SQL/HTML/메시지 템플릿 엔진을 설계할 때
- "값"과 "문자열화 정책"을 분리하고 싶을 때

예제:

- `examples/py314_template_strings.py`

### 3. 인터프리터 API와 `InterpreterPoolExecutor`

3.14는 서브인터프리터를 표준 라이브러리에서 만질 수 있는 길을 크게 넓혔다.

왜 중요하나:

- 하나의 프로세스 안에서 여러 인터프리터를 분리해 돌리면 상태 격리와 병렬성 사이에서 새로운 선택지가 생긴다.
- 멀티프로세스보다 가벼울 수 있고, 스레드보다 격리가 강하다.

중요한 제약:

- 각 인터프리터는 별도 상태를 가진다.
- 모듈 전역, 캐시, mutable 객체를 "그냥 공유"하는 모델이 아니다.

실무 포인트:

- CPU 바운드 작업을 바로 전부 바꾸는 만능 해법은 아니다.
- 하지만 Python의 병렬 실행 전략이 `threading vs multiprocessing` 2지선다에서 더 넓어졌다는 점이 중요하다.

예제:

- `examples/py314_interpreter_pool.py`

### 4. incremental cyclic garbage collection

이건 표면 문법보다 런타임 관점에서 더 중요하다.

왜 좋은가:

- CPython은 참조 카운팅 덕분에 많은 객체를 즉시 회수하지만, 순환 참조는 별도 cyclic GC가 담당한다.
- 큰 컬렉션 주기에서 pause가 문제될 수 있는데, 3.14는 이 사이클 컬렉션을 더 잘게 쪼개 처리하는 방향으로 개선했다.

의미:

- 지연 시간 민감한 워크로드에서 stop-the-world 성격의 부담을 완화하려는 흐름으로 읽으면 된다.

한 줄 정리:

- 3.14는 "문자열, 어노테이션, 병렬성, GC"처럼 언어 외곽으로 보이던 주제들이 표면 API로 올라온 버전이다.

## 지금 바로 체감이 큰 것만 꼽으면

실무 우선순위는 보통 이렇게 잡는 편이 좋다.

1. 3.10 `match`, `X | Y`, `zip(strict=True)`
2. 3.11 `TaskGroup`, `ExceptionGroup`, 성능 개선
3. 3.12 제네릭 문법, `type` 별칭, `sys.monitoring`
4. 3.13 free-threaded/JIT는 개념과 방향성 이해
5. 3.14 어노테이션/인터프리터/template string은 프레임워크/도구 관심이 있으면 깊게

## 학습 순서 추천

### 1단계: 문법과 실무 생산성

- 3.10 `match`
- 3.10 typing 개선
- 3.11 `TaskGroup`, `ExceptionGroup`

### 2단계: 타입 시스템 현대화

- 3.12 제네릭 문법
- 3.13 타입 파라미터 기본값
- 3.14 지연 평가 어노테이션

### 3단계: 런타임/도구 제작 시점

- 3.11 바이트코드 특수화
- 3.12 `sys.monitoring`
- 3.13 free-threaded/JIT
- 3.14 인터프리터 API와 incremental GC

## 이 저장소 예제 맵

| 버전 | 파일 |
| --- | --- |
| 3.10 | `examples/py310_pattern_matching.py`, `examples/py310_typing_and_zip_strict.py` |
| 3.11 | `examples/py311_exception_groups_and_taskgroup.py`, `examples/py311_tomllib.py` |
| 3.12 | `examples/py312_type_params.py`, `examples/py312_sys_monitoring.py` |
| 3.13 | `examples/py313_type_defaults_and_deprecated.py`, `examples/py313_runtime_modes.py` |
| 3.14 | `examples/py314_annotationlib.py`, `examples/py314_template_strings.py`, `examples/py314_interpreter_pool.py` |

## 마지막 정리

이 구간을 공부할 때 가장 중요한 포인트는 "버전별 기능 암기"가 아니다. 더 중요한 건 아래 다섯 가지다.

1. Python은 3.10 이후 분기와 타입 문법이 훨씬 선언적으로 바뀌었다.
2. Python은 3.11 이후 실행기 성능과 async 오류 모델이 확실히 좋아졌다.
3. Python은 3.12 이후 tooling 친화적 인터프리터가 되고 있다.
4. Python은 3.13 이후 GIL 이후의 런타임을 공개적으로 실험하고 있다.
5. Python은 3.14에서 프레임워크/도구 제작자가 좋아할 API를 많이 표면화했다.

## 공식 자료

- Python 3.10: [What's New In Python 3.10](https://docs.python.org/3/whatsnew/3.10.html)
- Python 3.11: [What's New In Python 3.11](https://docs.python.org/3/whatsnew/3.11.html)
- Python 3.12: [What's New In Python 3.12](https://docs.python.org/3/whatsnew/3.12.html)
- Python 3.13: [What's New In Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)
- Python 3.14: [What's New In Python 3.14](https://docs.python.org/3/whatsnew/3.14.html)
- PEP 634: [Structural Pattern Matching](https://peps.python.org/pep-0634/)
- PEP 654: [Exception Groups and `except*`](https://peps.python.org/pep-0654/)
- PEP 659: [Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/)
- PEP 695: [Type Parameter Syntax](https://peps.python.org/pep-0695/)
- PEP 703: [Making the GIL Optional](https://peps.python.org/pep-0703/)
- PEP 734: [Multiple Interpreters in the Stdlib](https://peps.python.org/pep-0734/)
- PEP 649: [Deferred Evaluation of Annotations](https://peps.python.org/pep-0649/)
- PEP 750: [Template Strings](https://peps.python.org/pep-0750/)
