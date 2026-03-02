# CPython 내부 동작과 Go 런타임 비교

이 문서는 "Python을 다시 깊게 공부할 때 내부 모델을 어떻게 잡아야 하는가"에 초점을 둔다. 비교 대상은 CPython과 Go 런타임이다.

핵심만 먼저 말하면:

- CPython은 동적 객체 모델 + 바이트코드 인터프리터 + 참조 카운팅 중심 메모리 관리
- Go는 정적 타입 + 네이티브 코드 + 고루틴 스케줄러 + 동시 마크-스윕 GC

둘 다 "고수준 언어 런타임"이지만 비용 구조가 완전히 다르다.

## 1. 코드가 실행되기까지

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

## 2. 객체 모델

### CPython

Python 객체는 매우 균일한 공통 헤더 모델을 가진다.

- 거의 모든 값은 객체다.
- 객체는 "참조 카운트 + 타입 포인터" 성격의 헤더를 가진다.
- 실제 연산은 타입 객체가 가진 슬롯/메서드 테이블을 타고 간다.

이 구조의 장점:

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

## 3. 메모리 관리

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

## 4. 동시성 모델

### CPython 표준 빌드

가장 중요한 사실:

- 기본 CPython은 한 프로세스 안에서 GIL 때문에 한 시점에 하나의 스레드만 Python 바이트코드를 실행한다.

이 말의 의미:

- I/O 바운드 작업에서는 `threading`이 여전히 유용하다.
- CPU 바운드 Python 코드에서는 스레드만으로 병렬 속도 향상을 기대하기 어렵다.

그래서 Python은 보통 이렇게 전략을 나눈다.

- I/O 바운드: `asyncio`, `threading`
- CPU 바운드: `multiprocessing`, 네이티브 확장, 벡터화 라이브러리

### CPython의 새 방향

3.12~3.14에서 중요한 흐름:

- per-interpreter GIL 기반 정비
- 3.13 free-threaded 빌드 실험
- 3.14 multiple interpreters 표준 라이브러리 지원 강화

즉, Python도 병렬 실행 전략을 넓히고 있다. 다만 아직 Go처럼 "기본값이 곧 병렬 고루틴"은 아니다.

### Go

Go의 핵심 실행 단위는 goroutine이다.

- goroutine은 OS thread보다 훨씬 가볍다.
- 런타임 스케줄러가 M:P:G 모델로 goroutine을 분배한다.
- 여러 코어에서 진짜 병렬 실행이 자연스럽다.

Python과의 체감 차이:

- Python의 `asyncio`는 협력적 스케줄링이다.
- Go goroutine은 런타임이 선점/스케줄링하는 더 "런타임 주도" 모델이다.

## 5. 함수 호출과 스택

### CPython

- 함수 호출은 새 frame object와 지역 변수 슬롯, 평가 스택 문맥을 동반한다.
- 호출 자체가 무겁다.
- 재귀나 잦은 작은 함수 분해는 가독성은 좋지만 성능상 비용이 있다.

3.11 이후 일부 경로가 빨라졌어도 기본 성격은 크게 변하지 않았다.

### Go

- goroutine은 작게 시작하는 growable stack을 가진다.
- 함수 호출 비용이 훨씬 낮고, 컴파일러 인라이닝도 기대할 수 있다.

따라서 같은 "작은 함수 수천만 번 호출"이더라도 비용 구조가 매우 다르다.

## 6. 예외와 에러

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

즉, Python은 "동적 객체 비용을 어떻게 덜 밟을까"가 크고, Go는 "힙/스케줄러/락 비용을 어떻게 낮출까"가 더 크다.

## 8. Python을 내부까지 공부할 때 추천 관측 포인트

이 저장소 예제와 함께 아래 내장 도구를 많이 보는 편이 좋다.

- `dis`: 바이트코드 보기
- `ast`: 파서가 만든 트리 보기
- `inspect`: 시그니처, 프레임, 소스 보기
- `gc`: GC 상태와 수집 횟수 보기
- `sys.monitoring`: 3.12+ 이벤트 관측
- `annotationlib`: 3.14 어노테이션 평가 포맷 보기

## 9. 한 문장 비교

- CPython은 "동적 객체를 풍부하게 다루기 좋은 실행기"
- Go는 "정적 타입 위에서 병렬성과 처리량을 안정적으로 뽑기 좋은 런타임"

둘 중 누가 더 좋다는 문제가 아니라, "어떤 비용을 런타임이 대신 떠안는가"가 다르다.

## 공식 자료

- Python execution model: [docs.python.org/reference/executionmodel.html](https://docs.python.org/3/reference/executionmodel.html)
- Python data model: [docs.python.org/reference/datamodel.html](https://docs.python.org/3/reference/datamodel.html)
- Python C API memory management: [docs.python.org/c-api/memory.html](https://docs.python.org/3/c-api/memory.html)
- PEP 703: [Making the Global Interpreter Lock Optional](https://peps.python.org/pep-0703/)
- PEP 734: [Multiple Interpreters in the Stdlib](https://peps.python.org/pep-0734/)
- Go FAQ implementation note: [go.dev/doc/faq](https://go.dev/doc/faq)
- Go runtime internals note: [go/src/runtime/HACKING.md](https://go.dev/src/runtime/HACKING.md)
- Go GC guide: [go.dev/doc/gc-guide](https://go.dev/doc/gc-guide)
