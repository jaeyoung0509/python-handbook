# Cancellation and TaskGroup

<p class="lead">async 코드의 품질은 "얼마나 잘 동시에 돌리는가"보다 "얼마나 잘 취소하고 정리하는가"에서 갈린다. `CancelledError`는 일반 에러가 아니라 제어 흐름의 일부이고, `TaskGroup`은 그 취소/정리 규칙을 구조적으로 묶어준다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 취소는 예외 전파로 모델링된다. cleanup이 필요하면 `try/finally` 또는 `except asyncio.CancelledError`에서 정리한 뒤 다시 `raise`해야 한다. 여러 task를 같이 다루는 경우 `TaskGroup`이 가장 안전한 기본값이다.</p>
</div>

## 구조적 동시성 그림

<MermaidDiagram
  caption="timeout이나 자식 task 실패가 발생하면 TaskGroup은 관련 task를 취소하고, 남은 예외를 ExceptionGroup으로 보고한다."
  chart="flowchart LR; A[Parent task] --> B[TaskGroup]; B --> C[child task A]; B --> D[child task B]; C --> E[failure or timeout]; E --> F[cancel siblings]; F --> G[cleanup in finally]; G --> H[ExceptionGroup or normal exit];"
/>

## 취소를 제대로 처리하는 코드

```py
import asyncio


async def worker(name: str) -> None:
    try:
        while True:
            print(f"{name}: tick")
            await asyncio.sleep(0.2)
    except asyncio.CancelledError:
        print(f"{name}: cleanup")
        raise


async def main() -> None:
    try:
        async with asyncio.timeout(0.6):
            async with asyncio.TaskGroup() as task_group:
                task_group.create_task(worker("alpha"))
                task_group.create_task(worker("beta"))
    except TimeoutError:
        print("timeout reached")


asyncio.run(main())
```

<p class="code-caption">`asyncio.timeout()`은 블록 밖으로 `TimeoutError`를 던지지만, 내부적으로는 관련 task에 cancellation을 전달한다. 각 worker는 cleanup 후 `CancelledError`를 다시 올려야 TaskGroup의 취소 규칙이 깨지지 않는다.</p>

## `CancelledError`를 삼키면 왜 위험한가

- 상위 task가 "이미 취소되었다"는 사실을 잃어버린다.
- graceful shutdown 시 정리 순서가 꼬인다.
- timeout과 parent cancellation이 정상적으로 끝나지 않는다.

## `TaskGroup`이 주는 이점

- 자식 task의 생명주기를 블록 경계에 묶는다.
- 하나가 실패하면 나머지를 자동 취소한다.
- 종료 시 예외를 `ExceptionGroup`으로 구조화해 보존한다.

## graceful shutdown 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>cleanup은 finally</h3>
    <p>파일, 소켓, semaphore, queue consumer 정리는 `finally`에서 처리하는 편이 안전하다.</p>
  </div>
  <div class="check-card">
    <h3>CancelledError 재전파</h3>
    <p>특별한 이유가 없으면 cleanup 후 다시 올린다. 삼키는 순간 상위 제어 흐름이 망가진다.</p>
  </div>
  <div class="check-card">
    <h3>TaskGroup 우선</h3>
    <p>새 코드에서는 흩어진 `create_task()`보다 `TaskGroup`을 기본값으로 두는 편이 안전하다.</p>
  </div>
  <div class="check-card">
    <h3>timeout을 설계에 포함</h3>
    <p>정상 경로만큼 timeout 경로를 중요하게 다룬다. 특히 fan-out API 호출에 필수다.</p>
  </div>
</div>

## 공식 자료

- [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- [Task Groups](https://docs.python.org/3/library/asyncio-task.html#task-groups)

## 실전 연결

- API fan-out
- graceful shutdown
- background worker stop sequence
