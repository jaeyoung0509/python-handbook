# Testing and Debugging

<p class="lead">async 버그는 순서와 타이밍 문제라서, 실패가 매번 재현되지 않을 수 있다. 그래서 asyncio 코드는 "테스트가 있다"보다 "timeout, leak check, debug mode, cancellation path 검증이 있다"가 더 중요하다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: async 테스트는 정상 결과만 확인하면 부족하다. timeout으로 hang를 잡고, debug mode로 잘못된 await와 느린 callback을 드러내고, 남은 task가 없는지 확인해야 한다.</p>
</div>

## 관측 흐름

<MermaidDiagram
  caption="async 디버깅은 증상 재현보다 관측이 중요하다. timeout, debug mode, task inspection으로 상태를 드러내야 한다."
  chart="flowchart LR; A[Test or local repro] --> B[timeout guard]; B --> C[debug mode]; C --> D[inspect pending tasks]; D --> E[fix cleanup, cancellation, blocking path];"
/>

## 가장 먼저 넣을 수 있는 가드

```py
import asyncio


async def fetch_with_guard() -> str:
    async with asyncio.timeout(0.5):
        await asyncio.sleep(0.1)
        return "ok"


async def main() -> None:
    runner = asyncio.Runner(debug=True)
    with runner:
        print(runner.run(fetch_with_guard()))


if __name__ == "__main__":
    main()
```

<p class="code-caption">`asyncio.timeout()`은 hang를 테스트 실패로 빠르게 바꾸고, `Runner(debug=True)` 또는 `asyncio.run(..., debug=True)`는 debug 모드에서 추가 경고와 관측 포인트를 연다.</p>

## task leak를 보는 간단한 패턴

```py
import asyncio


async def assert_no_extra_tasks() -> None:
    current = asyncio.current_task()
    leaked = {
        task
        for task in asyncio.all_tasks()
        if task is not current and not task.done()
    }
    if leaked:
        raise AssertionError(f"leaked tasks: {leaked}")
```

## debug mode에서 특히 드러나는 것

- 잊힌 await
- thread-safe 하지 않은 loop API 사용
- 너무 오래 걸리는 callback / selector operation
- 닫히지 않은 transport와 resource 경고

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>모든 테스트에 timeout</h3>
    <p>hang는 실패보다 더 나쁘다. 타임아웃으로 반드시 끝나게 만든다.</p>
  </div>
  <div class="check-card">
    <h3>cleanup path 검증</h3>
    <p>취소 시에도 queue, semaphore, background task가 정상 정리되는지 본다.</p>
  </div>
  <div class="check-card">
    <h3>debug mode 활용</h3>
    <p>로컬 재현과 CI 디버깅에서 debug 모드를 켜면 잘못된 await와 느린 callback을 더 빨리 드러낼 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>pending task 검사</h3>
    <p>테스트가 끝난 뒤 남은 task가 없는지 확인하면 task leak를 조기에 잡을 수 있다.</p>
  </div>
</div>

## 공식 자료

- [Developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html)
- [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
