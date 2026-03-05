# CPython Internals Advanced

<p class="lead">이 페이지는 CPython 내부를 "성능 튜닝 팁"이 아니라 실행 구조로 이해하기 위한 심화 노트다. source -> AST -> code object -> frame -> eval loop -> object/memory 경계를 하나로 묶어 보면, 추상적인 "느리다/빠르다" 대신 어디서 비용이 생기는지 설명할 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: CPython 내부를 읽는 핵심은 세 층이다. 실행 층(frame/code/bytecode), 객체 층(PyObject/refcount/type), 메모리 층(refcount + cycle GC + allocator). 여기에 `dis`, `ast`, `gc`, `tracemalloc`, `sys.monitoring` 실험을 붙이면 runtime 감각이 급격히 올라간다.</p>
</div>

## 실행 파이프라인

<MermaidDiagram
  caption="Python 코드는 해석기 내부에서 여러 단계로 변환/실행된다."
  chart="flowchart LR; A[&quot;Source code&quot;] --> B[&quot;AST&quot;]; B --> C[&quot;Code object&quot;]; C --> D[&quot;Frame object&quot;]; D --> E[&quot;Bytecode eval loop&quot;]; E --> F[&quot;PyObject operations&quot;];"
/>

## 1) code object와 frame을 구분해야 한다

- code object: 정적 실행 계획(상수, 변수명, 바이트코드)
- frame object: 실행 시점 문맥(로컬 변수, 스택, 현재 instruction 위치)
- 같은 함수라도 호출마다 새 frame이 생긴다.

```py
import inspect


def sample(x: int, y: int) -> int:
    frame = inspect.currentframe()
    assert frame is not None
    print("frame locals keys:", list(frame.f_locals))
    return x + y
```

## 2) bytecode specialization은 "항상 빠름"이 아니라 "안정적 패턴에서 이득"

- 3.11+에서는 adaptive interpreter가 hot opcode를 specialization한다.
- polymorphic access가 심한 경로에서는 specialization 이득이 줄 수 있다.
- `dis.dis()`로 비교해보면 학습이 빠르다.

```py
import dis


def add_loop(n: int) -> int:
    total = 0
    for i in range(n):
        total += i
    return total


dis.dis(add_loop)
```

## 3) 메모리 모델: refcount + cycle GC

<MermaidDiagram
  caption="CPython 메모리 회수는 즉시 회수(refcount)와 순환 회수(cyclic GC)의 조합이다."
  chart="flowchart LR; A[&quot;Object refcount reaches 0&quot;] --> B[&quot;Immediate deallocation&quot;]; C[&quot;Reference cycle remains&quot;] --> D[&quot;Generational GC scan&quot;]; D --> E[&quot;Cycle collected&quot;];"
/>

- 많은 객체는 refcount 0이 되는 즉시 회수된다.
- cycle이 있으면 refcount만으로는 회수되지 않아 GC가 필요하다.
- `__del__`이 개입하면 회수 타이밍/순서가 복잡해질 수 있다.

## 4) 관찰 도구를 습관화한다

| 도구 | 용도 | 언제 쓰나 |
| --- | --- | --- |
| `dis` | 바이트코드 확인 | 실행 경로/연산 패턴 확인 |
| `ast` | 구문 트리 확인 | 코드 생성/변환/분석 |
| `gc` | GC 상태/수집 | cycle 의심, 메모리 튜닝 |
| `tracemalloc` | 할당 추적 | 누수/증가 경로 추적 |
| `sys.monitoring` | 저비용 이벤트 훅 | 런타임 이벤트 관찰 실험 |

## 5) GIL/free-threaded/subinterpreter를 같은 축에서 본다

- 기본 CPython: GIL이 bytecode 병렬 실행을 제한
- free-threaded build(실험/진화 중): 병렬성 trade-off가 달라짐
- subinterpreter: isolation과 병렬성의 절충안

여기서 중요한 건 "어떤 모델이 더 빠른가"보다 "어떤 공유/격리 비용을 감수하는가"다.

## 실험 루틴 추천

1. `dis`로 함수 2개 비교
2. `tracemalloc`으로 할당 top 라인 추적
3. cycle 객체를 만들어 `gc.collect()` 결과 관찰
4. 가능하면 `sys.monitoring` 이벤트를 짧게 수집

이 저장소에는 위 루틴을 바로 실행할 수 있는 `examples/cpython_runtime_labs.py`를 추가했다.

## 자주 하는 실수

- refcount와 GC를 같은 것으로 생각한다.
- 단일 micro-benchmark 결과를 전체 성능 결론으로 일반화한다.
- bytecode 하나 보고 실제 병목을 단정한다.
- 프레임워크 레벨 I/O 비용을 무시한 채 인터프리터 비용만 본다.

## 같이 읽으면 좋은 페이지

- [Execution Model](/runtime/execution-model)
- [Memory and GC](/runtime/memory-and-gc)
- [Bytecode and Specialization](/runtime/bytecode-and-specialization)
- [CPython vs Go Runtime](/cpython-vs-go-runtime)

## 공식 자료

- [dis](https://docs.python.org/3/library/dis.html)
- [ast](https://docs.python.org/3/library/ast.html)
- [gc](https://docs.python.org/3/library/gc.html)
- [tracemalloc](https://docs.python.org/3/library/tracemalloc.html)
- [sys.monitoring](https://docs.python.org/3/library/sys.monitoring.html)
- [CPython Developer Guide](https://devguide.python.org/internals/interpreter/)
