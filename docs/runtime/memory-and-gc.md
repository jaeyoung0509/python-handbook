# Memory and GC

<p class="lead">Python은 refcount와 cyclic GC를 같이 쓰기 때문에, Go/Java 같은 tracing GC 언어와 메모리 감각이 꽤 다르다. 많은 객체는 refcount가 0이 되는 즉시 사라지지만, cycle은 별도 GC가 모아서 정리한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: CPython 메모리 모델의 핵심은 "즉시 회수되는 refcount"와 "cycle만 따로 도는 GC"의 조합이다. 그래서 자원 정리 시점은 꽤 예측 가능하지만, 큰 cycle graph와 pause 특성은 별도로 신경 써야 한다.</p>
</div>

## 메모리 회수 흐름

<MermaidDiagram
  caption="대부분의 객체는 refcount가 0이 되면 바로 회수된다. 서로 참조하는 cycle은 별도 cyclic GC가 찾아서 정리한다."
  chart="flowchart LR; A[object created] --> B[reference count changes]; B --> C{refcount == 0?}; C -->|yes| D[immediate deallocation]; C -->|no| E[possible cycle survives]; E --> F[cyclic GC scan]; F --> G[cycle reclaimed];"
/>

## cycle을 만드는 간단한 예

```py
import gc


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.other: Node | None = None


left = Node("left")
right = Node("right")
left.other = right
right.other = left

del left
del right

print("collected objects:", gc.collect())
```

<p class="code-caption">`left`와 `right`는 서로를 가리키는 cycle을 만든다. 외부 참조가 사라져도 refcount만으로는 0이 되지 않기 때문에 cyclic GC가 개입해야 한다.</p>

## `pymalloc` 감각

- CPython은 작은 객체를 위해 별도 allocator(`pymalloc`)를 사용한다.
- "객체가 해제되었다"와 "운영체제에 메모리가 즉시 반환되었다"는 같은 뜻이 아니다.
- 따라서 Python 프로세스 RSS가 기대만큼 바로 줄지 않는다고 해서 곧바로 leak로 단정하면 안 된다.

## 3.14에서 읽어야 할 흐름

- cyclic GC pause를 더 잘게 나누려는 방향
- latency-sensitive workload에서 stop-the-world 부담을 줄이려는 시도
- free-threaded/runtime 진화와 함께 메모리 모델도 점진적으로 조정되는 흐름

## 실전 연결

- large object graph
- file/socket lifecycle
- memory leak debugging

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>자원 정리는 GC에 기대지 않는다</h3>
    <p>파일, 소켓, 세션은 `with`나 명시적 close로 닫는 편이 안전하다. 메모리 회수와 자원 회수는 같은 문제가 아니다.</p>
  </div>
  <div class="check-card">
    <h3>cycle을 의식한다</h3>
    <p>복잡한 graph 구조나 listener/reference back-pointer 패턴은 cycle을 만들기 쉽다.</p>
  </div>
  <div class="check-card">
    <h3>RSS만 보지 않는다</h3>
    <p>allocator 특성 때문에 프로세스 메모리 사용량은 즉시 줄지 않을 수 있다. object count와 allocation pattern도 같이 본다.</p>
  </div>
  <div class="check-card">
    <h3>GC debug 도구를 쓴다</h3>
    <p>`gc` 모듈, tracemalloc, object graph inspection을 같이 써야 leak와 allocator 특성을 구분하기 쉽다.</p>
  </div>
</div>

## 공식 자료

- [gc](https://docs.python.org/3/library/gc.html)
- [Garbage collector design](https://github.com/python/cpython/blob/main/InternalDocs/garbage_collector.md)
