# GIL and Subinterpreters

<p class="lead">이 주제는 Python의 병렬성 논쟁 거의 전부와 연결된다. thread, async, process, subinterpreter, free-threaded build는 서로 대체 관계가 아니라, "어떤 상태를 공유할 것인가"와 "어디까지 병렬로 돌릴 것인가"라는 다른 선택지다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 전통적인 CPython에서 GIL은 한 interpreter 안의 Python bytecode 병렬 실행을 제한한다. I/O bound workload는 thread가 여전히 유용할 수 있지만, CPU bound 병렬성은 process나 새로운 interpreter/free-threaded 옵션을 더 신중하게 봐야 한다.</p>
</div>

## 병렬성 선택지를 한 그림으로 보기

<MermaidDiagram
  caption="Python의 동시성/병렬성 선택지는 하나가 아니라 여러 층이다. 공유 상태와 격리 강도가 다르다."
  chart="flowchart LR; A[threading] --> B[shared process state]; C[asyncio] --> B; D[multiprocessing] --> E[separate process state]; F[subinterpreters] --> G[separate interpreter state in one process];"
/>

## GIL이 정확히 막는 것

- 하나의 interpreter 안에서 여러 thread가 Python bytecode를 동시에 실행하는 것
- 단, 많은 I/O operation과 일부 C extension은 GIL을 잠시 놓을 수 있다
- 그래서 "thread는 쓸모없다"가 아니라 "CPU-bound pure Python 병렬성에는 한계가 크다"가 더 정확하다

## `InterpreterPoolExecutor`가 의미하는 것

```py
from concurrent.futures import InterpreterPoolExecutor


def square(value: int) -> int:
    return value * value


with InterpreterPoolExecutor(max_workers=2) as pool:
    print(list(pool.map(square, [1, 2, 3, 4])))
```

<p class="code-caption">subinterpreter는 하나의 프로세스 안에 여러 interpreter state를 둔다. thread보다 격리가 강하고 process보다 가벼울 수 있지만, 모듈 전역이나 mutable object를 "그냥 공유"하는 모델은 아니다.</p>

## 언제 어떤 선택지가 맞는가

| 선택지 | 잘 맞는 경우 | 주의점 |
| --- | --- | --- |
| `threading` | I/O wait가 많고 상태 공유가 필요할 때 | CPU-bound pure Python 병렬성은 제한적 |
| `asyncio` | I/O multiplexing과 구조적 동시성이 중요할 때 | CPU 작업은 별도 offload 필요 |
| `multiprocessing` | 강한 격리와 CPU 병렬성 필요 | 프로세스 비용과 IPC 부담 |
| subinterpreter | process보다 가볍고 thread보다 격리가 필요할 때 | 공유 모델과 라이브러리 호환성 숙지 필요 |

## free-threaded build는 무엇으로 봐야 하나

- 아직 기본 배포 모드가 아니다
- 생태계 호환성과 성능 trade-off가 중요하다
- "이제 GIL 문제 끝"보다 "Python runtime의 병렬성 설계가 바뀌는 중"으로 읽는 편이 정확하다

## 실전 연결

- thread를 써도 되는 경우
- process가 더 나은 경우
- 3.14 `InterpreterPoolExecutor`를 어디까지 기대해도 되는지

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>공유 상태가 필요한가</h3>
    <p>상태 공유가 핵심이면 thread, 격리가 핵심이면 process나 subinterpreter가 더 맞을 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>CPU-bound인가 I/O-bound인가</h3>
    <p>이 구분이 가장 먼저다. pure Python CPU 작업을 thread로 분산한다고 항상 빨라지지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>라이브러리 호환성을 확인했는가</h3>
    <p>특히 subinterpreter나 free-threaded 빌드는 써드파티 라이브러리 호환성을 확인해야 한다.</p>
  </div>
  <div class="check-card">
    <h3>직렬화/통신 비용을 봤는가</h3>
    <p>process와 interpreter 경계가 생기면 전달 비용과 상태 분할 비용을 같이 본다.</p>
  </div>
</div>

## 공식 자료

- [concurrent.interpreters](https://docs.python.org/3/library/concurrent.interpreters.html)
- [What's New in Python 3.14](https://docs.python.org/3/whatsnew/3.14.html)
- [PEP 703](https://peps.python.org/pep-0703/)
