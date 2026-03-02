# CPython 내부 동작과 Go 런타임 비교

이 문서는 "Python을 다시 깊게 공부할 때 내부 모델을 어떻게 잡아야 하는가"에 초점을 둔다. 비교 대상은 CPython과 Go 런타임이다.

전제:

- 여기서 말하는 Python은 CPython 기준이다.
- "Python 언어"와 "CPython 구현체"는 완전히 같은 말이 아니다.
- 메모리, GIL, refcount, subinterpreter 같은 이야기는 대부분 CPython 구현체 관점이다.

## 먼저 결론부터

핵심만 바로 말하면 이렇다.

- CPython은 동적 객체 모델 + 바이트코드 인터프리터 + 참조 카운팅 중심 메모리 관리
- Go는 정적 타입 + 네이티브 코드 + 고루틴 스케줄러 + 동시 mark-sweep GC

둘 다 "고수준 언어 런타임"이지만, 비용이 발생하는 위치가 완전히 다르다.

## 한눈에 비교

| 항목 | CPython | Go | 실무에서 느끼는 차이 |
| --- | --- | --- | --- |
| 실행 방식 | 바이트코드 인터프리터 | AOT 네이티브 컴파일 | Python은 호출/조회 비용이 더 동적이다 |
| 타입 모델 | 동적 타입 | 정적 타입 | Python은 유연하고, Go는 예측 가능성이 높다 |
| 메모리 관리 | refcount + cyclic GC | concurrent tracing GC | Python은 즉시 해제 감각이 있고, Go는 tracing 부담이 있다 |
| 동시성 | 기본 빌드는 GIL 영향 | goroutine + scheduler | Go는 CPU 병렬성이 기본값에 가깝다 |
| 함수 호출 | 상대적으로 무거움 | 상대적으로 가벼움 | Python은 작은 함수/객체가 쌓일수록 불리해질 수 있다 |
| 오류 처리 | 예외 중심 | error value 중심 | Python은 풍부한 traceback, Go는 명시적 흐름 |
| 최적화 포인트 | 객체 수, lookup, Python loop | allocation, GC, lock, scheduler | 병목 보는 관점 자체가 다르다 |

## 이 문서를 읽는 법

- Go 배경이 있고 Python 내부가 낯설다:
  - `한눈에 비교` -> `동시성 모델` -> `메모리 관리`
- Python은 쓰지만 런타임 감각이 약하다:
  - `코드가 실행되기까지` -> `객체 모델` -> `함수 호출과 스택`
- 면접/설명용으로 요약이 필요하다:
  - `자주 헷갈리는 포인트`와 `한 문장 비교`만 먼저 읽어도 된다.

## 자주 헷갈리는 포인트

1. Python의 GIL은 "Python이 스레드를 못 쓴다"는 뜻이 아니다.
   - I/O 바운드에서는 여전히 유용하다.
   - CPU 바운드 Python 바이트코드 병렬성이 제한된다는 뜻에 가깝다.
2. CPython의 메모리 관리는 "GC만 있는 언어"와 감각이 다르다.
   - refcount 때문에 객체가 바로 정리되는 순간이 많다.
   - 하지만 순환 참조는 별도 cyclic GC가 처리한다.
3. Python의 느림은 "인터프리터라서 느리다" 한 문장으로 끝나지 않는다.
   - 동적 객체 모델, attribute lookup, 함수 호출, boxing/unboxing 비슷한 간접 비용이 같이 작동한다.
4. Go의 빠름은 "무조건 네이티브라서 빠르다"도 아니다.
   - escape analysis, allocation, GC pressure, contention이 성능을 크게 좌우한다.

## 1. 코드가 실행되기까지

### 한 줄 비교

- CPython: "소스 -> AST -> 바이트코드 -> 인터프리터"
- Go: "소스 -> 타입체크/최적화 -> 네이티브 코드"

### CPython

대략 이런 단계를 거친다.

1. 소스 코드를 토큰화한다.
2. PEG parser가 파싱해 AST를 만든다.
3. 컴파일러가 심볼 테이블과 code object를 만든다.
4. code object 안의 바이트코드를 인터프리터가 실행한다.

중요한 특징:

- 실행 단위는 기계어가 아니라 바이트코드다.
- 함수 호출, 속성 접근, 전역 이름 조회, 객체 생성이 모두 동적 디스패치 비용을 가진다.
- 3.11 이후에는 바이트코드가 실행 중 특수화되지만, 본질적으로 인터프리터 기반이라는 사실은 그대로다.

### Go

Go는 기본적으로 ahead-of-time 컴파일 언어다.

1. 파싱/타입체크
2. SSA 기반 최적화
3. 네이티브 기계어 생성
4. 링크 후 실행

중요한 특징:

- 런타임은 있지만, 파이썬처럼 "매 바이트코드를 해석"하지 않는다.
- 타입 정보가 컴파일 시점에 더 많이 고정되므로 호출/메모리 접근 비용 예측성이 높다.

### 실무 번역

- Python에서 "함수 하나 더 쪼개는 비용"은 Go보다 무겁게 느껴질 수 있다.
- Python에서 attribute lookup과 동적 dispatch는 아주 흔한 병목이다.
- Go에서는 같은 문제를 볼 때 dispatch보다 allocation/escaping을 먼저 보는 경우가 많다.

## 2. 객체 모델

### 한 줄 비교

- CPython: "거의 모든 게 객체"
- Go: "값 레이아웃이 더 정적으로 정해진다"

### CPython

Python 객체는 매우 균일한 공통 헤더 모델을 가진다.

- 거의 모든 값은 객체다.
- 객체는 대체로 "참조 카운트 + 타입 포인터" 성격의 헤더를 가진다.
- 실제 연산은 타입 객체가 가진 슬롯/메서드 테이블을 타고 간다.

장점:

- 모든 것을 일관된 객체 모델로 다룰 수 있다.
- 런타임 리플렉션, 동적 디스패치, 메타클래스, monkey patching이 자연스럽다.

비용:

- 작은 정수 하나, 속성 조회 하나에도 메타데이터와 간접 참조가 붙는다.
- tight loop에서 오버헤드가 크다.

### Go

Go는 정적 타입 기반이다.

- 값이 스택에 놓일지 힙에 놓일지 컴파일러의 escape analysis가 크게 관여한다.
- 인터페이스/리플렉션은 가능하지만 Python처럼 기본 모델은 아니다.

장점:

- 값 레이아웃과 호출 비용이 더 안정적이다.
- 컴파일러 최적화 여지가 크다.

비용:

- 런타임에서 Python만큼 자유롭게 객체 구조를 바꾸는 감각은 아니다.

### 실무 번역

- Python의 유연성은 "객체 모델이 비싸도 풍부하다"는 전제를 가진다.
- Go는 그 반대로 "유연성을 제한하는 대신 예측 가능성을 얻는다"에 가깝다.

## 3. 메모리 관리

### 한 줄 비교

- CPython: "즉시 해제 + 순환 참조는 별도 GC"
- Go: "trace해서 살아 있는 객체를 찾는 GC"

### CPython: 참조 카운팅 + cyclic GC

CPython 메모리 모델은 두 층으로 보는 게 좋다.

1. 즉시 회수층
2. 순환 참조 회수층

즉시 회수층:

- 객체의 참조 카운트가 0이 되면 즉시 해제한다.
- 따라서 파일 핸들, 소켓, 작은 객체 수명이 비교적 예측 가능하다.

순환 참조 회수층:

- `a -> b -> a` 같은 구조는 참조 카운트만으로는 못 지운다.
- 별도의 cyclic GC가 컨테이너 객체 그래프를 순회해 회수한다.

메모리 할당기:

- 작은 객체는 `pymalloc`이 arena/pool/block 계층으로 관리한다.
- 큰 객체는 시스템 할당기로 내려갈 수 있다.

의미:

- CPython은 "짧은 객체를 빨리 만들고 지우는" 패턴은 꽤 강하다.
- 하지만 객체 수가 많고 그래프가 복잡하면 메모리 오버헤드와 GC 비용이 커질 수 있다.

### Go: 동시 mark-sweep GC

Go는 전역 참조 카운팅이 아니라 tracing GC를 쓴다.

- 루트에서 시작해 살아 있는 객체를 표시(mark)한다.
- 도달 불가능한 객체를 sweep한다.
- GC는 애플리케이션과 동시에(concurrent) 진행되도록 설계되어 있다.

장점:

- 순환 참조를 별도 모델 없이 자연스럽게 처리한다.
- 참조 카운트 갱신 비용이 없다.

비용:

- 힙이 커질수록 tracing 부담이 생긴다.
- 레이턴시와 처리량 사이의 균형을 GC가 계속 잡아야 한다.

### 실무 번역

- Python에서 파일/소켓 정리가 "생각보다 빨리" 일어나는 경험은 refcount 영향이 크다.
- Go에서는 finalizer나 GC 타이밍에 대한 기대를 더 보수적으로 잡는 편이 안전하다.
- Python은 객체 그래프가 복잡해지면 cyclic GC cost를, Go는 heap growth와 GC pressure를 먼저 본다.

## 4. 동시성 모델

### 한 줄 비교

- CPython 기본 빌드: "스레드는 편하지만 CPU 병렬 Python 실행은 제한적"
- Go: "가벼운 goroutine을 런타임이 적극적으로 스케줄링"

### CPython 표준 빌드

가장 중요한 사실:

- 기본 CPython은 한 프로세스 안에서 GIL 때문에 한 시점에 하나의 스레드만 Python 바이트코드를 실행한다.

이 말의 의미:

- I/O 바운드 작업에서는 `threading`이 여전히 유용하다.
- CPU 바운드 Python 코드에서는 스레드만으로 병렬 속도 향상을 기대하기 어렵다.

그래서 Python은 보통 이렇게 전략을 나눈다.

- I/O 바운드: `asyncio`, `threading`
- CPU 바운드: `multiprocessing`, 네이티브 확장, 벡터화 라이브러리

추가로 기억할 점:

- C extension이 GIL을 해제하는 동안에는 다른 스레드가 실행될 수 있다.
- 그래서 "Python 스레드는 무조건 CPU 병렬성이 0"이라고 단정하면 과하다.

### CPython의 새 방향

3.12~3.14에서 중요한 흐름:

- per-interpreter GIL 기반 정비
- 3.13 free-threaded 빌드 실험
- 3.14 multiple interpreters 표준 라이브러리 지원 강화

즉, Python도 병렬 실행 전략을 넓히고 있다. 다만 아직 Go처럼 "기본값이 곧 병렬 goroutine"은 아니다.

### Go

Go의 핵심 실행 단위는 goroutine이다.

- goroutine은 OS thread보다 훨씬 가볍다.
- 런타임 스케줄러가 M:P:G 모델로 goroutine을 분배한다.
- 여러 코어에서 진짜 병렬 실행이 자연스럽다.

Python과의 체감 차이:

- Python의 `asyncio`는 협력적 스케줄링이다.
- Go goroutine은 런타임이 선점/스케줄링하는 더 "런타임 주도" 모델이다.

### 실무 번역

- Python에서 비동기는 "작업을 잘 쪼개고 await를 잘 두는 것"이 중요하다.
- Go에서는 goroutine을 쉽게 늘릴 수 있지만, 그만큼 lock contention과 resource fan-out 관리가 중요하다.

## 5. 함수 호출과 스택

### 한 줄 비교

- CPython: 함수 호출이 상대적으로 무겁다.
- Go: 함수 호출이 상대적으로 가볍고 인라이닝 여지도 크다.

### CPython

- 함수 호출은 새 frame 문맥, 지역 변수 슬롯, 평가 스택 상태를 동반한다.
- 호출 자체가 무겁다.
- 재귀나 잦은 작은 함수 분해는 가독성은 좋지만 성능상 비용이 있다.

3.11 이후 일부 경로가 빨라졌어도 기본 성격은 크게 변하지 않았다.

### Go

- goroutine은 작게 시작하는 growable stack을 가진다.
- 함수 호출 비용이 훨씬 낮고, 컴파일러 인라이닝도 기대할 수 있다.

따라서 같은 "작은 함수 수천만 번 호출"이더라도 비용 구조가 매우 다르다.

### 실무 번역

- Python에서 "작은 헬퍼 함수를 아주 많이 쌓는 스타일"은 성능 민감 코드에서 손해일 수 있다.
- Go에서는 같은 상황에서 allocation과 escaping이 더 중요한 문제인 경우가 많다.

## 6. 예외와 에러

### 한 줄 비교

- CPython: 예외는 풍부하지만 비싸다.
- Go: error 값은 장황하지만 흐름이 명시적이다.

### CPython

- 예외는 정상 제어 흐름보다 비싸다.
- stack unwinding, traceback 생성, 객체 할당 비용이 있다.
- 대신 디버깅 정보가 풍부하다.

3.11의 `ExceptionGroup`은 "여러 실패를 보존하는 모델"을 추가했다는 점에서 중요하다.

### Go

- 일반 에러는 값으로 반환한다.
- panic/recover는 예외에 가까우나 일상적 오류 처리 도구가 아니다.

실무 감각:

- Python은 예외를 자주 쓰지만 hot path의 실패 제어 흐름으로 남용하면 비싸다.
- Go는 에러를 명시적으로 올리는 대신 코드가 장황해질 수 있다.

## 7. 성능 최적화 포인트도 다르다

### Python에서 먼저 보는 것

- 알고리즘 복잡도
- 객체 수 줄이기
- attribute lookup, Python-level loop 줄이기
- 표준 라이브러리/내장 함수/벡터화 라이브러리 사용
- CPU 바운드는 네이티브 코드나 프로세스/인터프리터 분리 고려

### Go에서 먼저 보는 것

- allocation 수
- escape analysis
- GC pressure
- lock contention
- goroutine 과잉 생성 여부

한 줄로 말하면:

- Python은 "동적 객체 비용을 어떻게 덜 밟을까"
- Go는 "힙/스케줄러/락 비용을 어떻게 낮출까"

## 8. Python을 내부까지 공부할 때 추천 관측 포인트

이 저장소 예제와 함께 아래 내장 도구를 많이 보는 편이 좋다.

- `dis`: 바이트코드 보기
- `ast`: 파서가 만든 트리 보기
- `inspect`: 시그니처, 프레임, 소스 보기
- `gc`: GC 상태와 수집 횟수 보기
- `sys.monitoring`: 3.12+ 이벤트 관측
- `annotationlib`: 3.14 어노테이션 평가 포맷 보기

추천 학습 흐름:

1. `ast`로 파싱 결과를 본다.
2. `dis`로 바이트코드를 본다.
3. `inspect`로 프레임/시그니처를 본다.
4. `gc`, `sys.monitoring`으로 런타임 이벤트를 관찰한다.

## 한 문장 비교

- CPython은 "동적 객체를 풍부하게 다루기 좋은 실행기"
- Go는 "정적 타입 위에서 병렬성과 처리량을 안정적으로 뽑기 좋은 런타임"

둘 중 누가 더 좋다는 문제가 아니라, "어떤 비용을 런타임이 대신 떠안는가"가 다르다.

## 공식 자료

- Python execution model: [docs.python.org/reference/executionmodel.html](https://docs.python.org/3/reference/executionmodel.html)
- Python data model: [docs.python.org/reference/datamodel.html](https://docs.python.org/3/reference/datamodel.html)
- Python C API memory management: [docs.python.org/3/c-api/memory.html](https://docs.python.org/3/c-api/memory.html)
- PEP 703: [Making the Global Interpreter Lock Optional](https://peps.python.org/pep-0703/)
- PEP 734: [Multiple Interpreters in the Stdlib](https://peps.python.org/pep-0734/)
- Go FAQ implementation note: [go.dev/doc/faq](https://go.dev/doc/faq)
- Go runtime internals note: [go.dev/src/runtime/HACKING.md](https://go.dev/src/runtime/HACKING.md)
- Go GC guide: [go.dev/doc/gc-guide](https://go.dev/doc/gc-guide)
