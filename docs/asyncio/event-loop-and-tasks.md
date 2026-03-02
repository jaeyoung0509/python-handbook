# Event Loop and Tasks

<p class="lead">`async/await`는 단순 문법이 아니라 스케줄링 계약이다. coroutine object는 아직 실행되지 않은 계산이고, task는 event loop가 스케줄링하는 실행 단위다. 이 구분이 흐려지면 `create_task()` 남용, 숨은 blocking 호출, 취소 누락 같은 문제가 곧바로 생긴다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: coroutine은 "실행 가능한 계획"이고, task는 "event loop에 올라간 실행 중인 일감"이다. event loop는 `await` 같은 양보 지점에서만 다른 task로 전환할 수 있으므로, blocking 호출 하나가 전체 시스템을 멈출 수 있다.</p>
</div>

## 먼저 구조를 그림으로

<MermaidDiagram
  caption="coroutine object는 바로 실행되지 않는다. task로 감싸지거나 await될 때 event loop가 스케줄링한다."
  chart="flowchart LR; A[async def call] --> B[coroutine object]; B --> C[await in parent task]; B --> D[create_task]; C --> E[event loop schedules work]; D --> E; E --> F[await suspension points]; F --> E;"
/>

## 왜 중요한가

- `create_task()`가 언제 안전하고 언제 누수의 시작인지 구분할 수 있다.
- sync blocking 함수가 왜 event loop 전체를 막는지 설명할 수 있다.
- FastAPI endpoint에서 async를 써도 내부가 blocking이면 왜 체감 이득이 없는지 이해할 수 있다.

## coroutine과 task를 구분하는 짧은 예제

```py
import asyncio
import time


def blocking_lookup() -> str:
    time.sleep(0.2)
    return "done"


async def child(name: str) -> str:
    await asyncio.sleep(0.1)
    return f"{name}-ok"


async def main() -> None:
    coro = child("plain")
    task = asyncio.create_task(child("scheduled"))

    print("coro type:", type(coro).__name__)
    print("task type:", type(task).__name__)

    result = await asyncio.to_thread(blocking_lookup)
    print("thread result:", result)
    print("task result:", await task)
    print("coro result:", await coro)


asyncio.run(main())
```

<p class="code-caption">`child("plain")`은 아직 coroutine object일 뿐이다. `create_task()`로 감싸거나 다른 task에서 `await`하기 전까지는 event loop가 이 일을 스케줄링하지 않는다. 반면 `blocking_lookup()` 같은 sync 함수는 `to_thread()`로 밀어내지 않으면 loop를 그대로 막는다.</p>

## `create_task()`를 직접 써도 되는 경우

- 현재 스코프보다 오래 살아야 하는 background work가 있고, 참조를 명시적으로 관리할 때
- 여러 task를 동시에 시작한 뒤 나중에 직접 await/join할 때
- framework가 아닌 애플리케이션 레벨에서 명시적 task lifecycle을 관리할 때

## `TaskGroup`이 더 나은 경우

- fan-out 요청처럼 task들의 생명주기가 하나의 블록에 묶일 때
- 하나가 실패하면 나머지도 같이 정리되어야 할 때
- 예외를 구조적으로 보고 싶을 때

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>blocking call 제거</h3>
    <p>`time.sleep`, sync DB driver, 무거운 CPU 작업은 event loop 안에서 직접 돌리지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>task owner 명확화</h3>
    <p>task를 만들었으면 누가 기다리고, 누가 취소하고, 누가 예외를 수거하는지 분명해야 한다.</p>
  </div>
  <div class="check-card">
    <h3>양보 지점 인식</h3>
    <p>전환은 `await`와 loop 내부 I/O 지점에서만 일어난다. 긴 CPU 루프는 async 함수 안에 있어도 cooperative하지 않다.</p>
  </div>
  <div class="check-card">
    <h3>thread offload 기준</h3>
    <p>기존 sync 라이브러리를 당장 교체 못 할 때는 `asyncio.to_thread()`나 executor를 검토한다.</p>
  </div>
</div>

## 공식 자료

- [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- [Runners](https://docs.python.org/3/library/asyncio-runner.html)
