# Python 3.10~3.14 Deep Dive

이 문서는 "Python 3.9 이후 감이 떨어진 상태에서 3.10~3.14를 한 번에 따라잡기"를 목표로 정리했다. 기준 구현체는 CPython이고, 예제는 이 저장소의 Python 3.14.3 환경에서 확인했다.

## 먼저 큰 흐름부터

3.10~3.14는 단순 문법 추가 구간이 아니다. 이 시기에는 다음 축이 동시에 움직였다.

- 언어 표현력: `match`, `X | Y`, 제네릭 문법, `type` 별칭, t-string
- 런타임 성능: 3.11의 적응형 바이트코드 특수화, 3.12의 comprehension inlining, 3.13의 실험적 JIT
- 동시성 모델: `ExceptionGroup`, `except*`, `TaskGroup`, 서브인터프리터, free-threaded 빌드
- 타입 시스템: `ParamSpec`, `TypeGuard`, 타입 파라미터 문법, 타입 파라미터 기본값
- 메타프로그래밍/툴링: `tomllib`, `sys.monitoring`, 지연 평가 어노테이션, `annotationlib`

정리하면:

- 3.10은 "문법 생산성"의 분기점
- 3.11은 "실행기와 비동기 오류 모델"의 분기점
- 3.12는 "타입 문법과 툴링 API"의 분기점
- 3.13은 "GIL 이후를 시험하는 런타임 모드"의 분기점
- 3.14는 "어노테이션/템플릿/멀티 인터프리터"를 표면 API까지 끌어올린 버전

## 버전별 핵심 요약

| 버전 | 한 줄 요약 | 특히 봐야 할 것 |
| --- | --- | --- |
| 3.10 | 오래된 `if/elif`, `typing` 불편함을 강하게 정리 | `match`, `|` 유니언, `ParamSpec`, `zip(strict=True)` |
| 3.11 | 속도와 구조적 예외 처리가 크게 바뀜 | PEP 659, `ExceptionGroup`, `except*`, `TaskGroup`, `tomllib` |
| 3.12 | 타입 시스템 문법이 현대화되고 관측 API가 열림 | PEP 695, PEP 701, PEP 709, `sys.monitoring`, per-interpreter GIL 기반 |
| 3.13 | GIL 없는 빌드와 JIT가 실험 단계로 등장 | PEP 703, PEP 744, PEP 667, PEP 696, PEP 702 |
| 3.14 | 어노테이션 평가 모델과 인터프리터 API가 실사용 단계로 진입 | PEP 649/749, PEP 734, PEP 750, incremental GC |

## Python 3.10

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

실무 포인트:

- 이벤트 디스패치, 파서, 도메인 상태 머신에서 강력하다.
- 단순 enum 분기만 있을 때는 `if/elif`가 더 읽기 좋을 수도 있다.
- 클래스 패턴은 데이터클래스와 궁합이 좋다.

예제:

- `examples/py310_pattern_matching.py`

### 2. 타입 표기 ergonomics 개선

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

예제:

- `examples/py310_typing_and_zip_strict.py`

### 3. 표준 라이브러리의 작은데 중요한 변화

- `zip(strict=True)`(PEP 618): 서로 길이가 다른 입력을 조용히 잘라먹지 않고 즉시 실패시킨다.
- 디버거/프로파일러용 정확한 라인 정보(PEP 626): 트레이싱 도구 정확도를 높였다.
- 에러 메시지가 더 구체적으로 바뀌기 시작했다.

실무 포인트:

- 데이터 파이프라인, ETL, 인덱스/레이블 동기화 코드에는 `zip(strict=True)`를 습관처럼 붙일 가치가 있다.

## Python 3.11

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

실무 포인트:

- fan-out/fan-in 비동기 처리, 배치 작업, 병렬 API 호출에서 반드시 알아야 한다.
- 기존 `except` 감각으로 보면 어색하지만, 실패를 보존한다는 점이 핵심이다.

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

3.11은 예외 위치와 traceback 품질도 좋아졌다. 특히 긴 표현식 안에서 어느 부분이 실패했는지 더 정확하게 가리킨다. 디버깅 경험이 3.10 이전보다 확실히 좋아진다.

## Python 3.12

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
- 일반 앱 개발자도 "Python이 관측 가능성(observability)을 언어 차원에서 더 신경 쓰기 시작했다"는 신호로 읽으면 된다.

예제:

- `examples/py312_sys_monitoring.py`

### 5. per-interpreter GIL 기반 마련

3.12는 "각 인터프리터가 자신의 GIL을 갖는 방향"을 위한 기반 작업이 들어간 버전이다. 곧바로 모든 코드가 병렬화되는 것은 아니지만, 이후 3.13 free-threaded와 3.14 interpreter API 노출로 이어지는 중요한 중간 단계다.

## Python 3.13

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

## Python 3.14

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

- 3.10
  - `examples/py310_pattern_matching.py`
  - `examples/py310_typing_and_zip_strict.py`
- 3.11
  - `examples/py311_exception_groups_and_taskgroup.py`
  - `examples/py311_tomllib.py`
- 3.12
  - `examples/py312_type_params.py`
  - `examples/py312_sys_monitoring.py`
- 3.13
  - `examples/py313_type_defaults_and_deprecated.py`
  - `examples/py313_runtime_modes.py`
- 3.14
  - `examples/py314_annotationlib.py`
  - `examples/py314_template_strings.py`
  - `examples/py314_interpreter_pool.py`

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
