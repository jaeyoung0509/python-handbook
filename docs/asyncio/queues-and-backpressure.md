# Queues and Backpressure

<p class="lead">async 시스템이 터지는 흔한 이유는 "너무 느려서"보다 "입력을 통제하지 못해서"다. producer는 계속 밀어 넣고 consumer는 못 따라가는데 큐 크기 제한도, 동시성 제한도, timeout도 없으면 메모리와 downstream이 먼저 무너진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: backpressure의 기본 도구는 `Queue(maxsize=...)`, `Semaphore`, timeout, 그리고 overload policy다. 무한 큐와 무한 fan-out은 초반엔 편하지만 운영 단계에서 가장 먼저 문제를 만든다.</p>
</div>

## 구조 그림

<MermaidDiagram
  caption="입력량을 통제하려면 큐 크기와 동시 실행 수를 같이 제한해야 한다. 큐는 burst를 흡수하고, semaphore는 downstream 동시 접근을 제어한다."
  chart="flowchart LR; A[Producer] --> B[Bounded Queue]; B --> C[Worker pool]; C --> D[Semaphore protected downstream]; D --> E[Remote API or DB];"
/>

## bounded queue와 graceful shutdown 예제

```py
import asyncio


async def producer(queue: asyncio.Queue[int]) -> None:
    for item in range(6):
        print("produce", item, "qsize before:", queue.qsize())
        await queue.put(item)
        print("enqueued", item, "qsize after:", queue.qsize())


async def worker(
    name: str,
    queue: asyncio.Queue[int],
    limiter: asyncio.Semaphore,
) -> None:
    try:
        while True:
            item = await queue.get()
            try:
                async with limiter:
                    await asyncio.sleep(0.15)
                    print(name, "handled", item)
            finally:
                queue.task_done()
    except asyncio.QueueShutDown:
        print(name, "shutdown")


async def main() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=2)
    limiter = asyncio.Semaphore(2)

    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(producer(queue))
        for index in range(3):
            task_group.create_task(worker(f"worker-{index}", queue, limiter))

        await queue.join()
        queue.shutdown()


asyncio.run(main())
```

<p class="code-caption">`maxsize=2`라서 producer는 queue가 꽉 차면 기다리게 된다. 이것이 가장 기본적인 backpressure다. Python 3.13+의 `Queue.shutdown()`은 worker를 더 깔끔하게 멈추는 데 유용하다.</p>

## backpressure를 설계할 때 정해야 할 것

- 입력을 기다리게 할 것인가 (`await queue.put`)
- 일정 시간 후 실패시킬 것인가 (`asyncio.timeout`)
- 오래된 작업을 버릴 것인가
- 여러 downstream 호출 수를 어떻게 제한할 것인가 (`Semaphore`)

## overload에 대한 기본 전략

<div class="doc-checklist">
  <div class="check-card">
    <h3>bounded queue</h3>
    <p>버스트를 흡수하되, 무한히 메모리를 잡아먹지 않게 한다.</p>
  </div>
  <div class="check-card">
    <h3>semaphore</h3>
    <p>큐가 있어도 downstream API/DB에 동시에 몇 개까지 보낼지 제한해야 한다.</p>
  </div>
  <div class="check-card">
    <h3>timeout</h3>
    <p>enqueue나 downstream 작업이 너무 오래 걸릴 때 언제 포기할지 기준을 둔다.</p>
  </div>
  <div class="check-card">
    <h3>drop policy</h3>
    <p>실시간 시스템은 "무조건 다 처리"보다 "낡은 작업을 버리고 최신 상태를 우선"하는 편이 맞는 경우도 많다.</p>
  </div>
</div>

## 실전 연결

- webhook processing
- rate-limited 외부 API fan-out
- background worker queue
- burst traffic ingestion

## 공식 자료

- [Queues](https://docs.python.org/3/library/asyncio-queue.html)
- [Synchronization Primitives](https://docs.python.org/3/library/asyncio-sync.html)
