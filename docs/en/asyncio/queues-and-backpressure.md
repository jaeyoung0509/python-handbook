# Queues and Backpressure

<p class="lead">Async systems often fail because they accept work faster than they can safely process it. Without queue limits, concurrency limits, and timeout policy, the first bottleneck is usually memory or a downstream dependency, not raw CPU speed.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: the foundation of backpressure is `Queue(maxsize=...)`, `Semaphore`, timeout, and an explicit overload policy. Unbounded queues and unbounded fan-out are easy to start with and hard to operate.</p>
</div>

## Backpressure Picture

<MermaidDiagram
  caption="Queue size absorbs bursts. Semaphore limits downstream concurrency. Both are needed for a stable async system."
  chart="flowchart LR; A[Producer] --> B[Bounded Queue]; B --> C[Worker pool]; C --> D[Semaphore protected downstream]; D --> E[Remote API or DB];"
/>

## Bounded Queue Example

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

<p class="code-caption">With `maxsize=2`, the producer is forced to slow down when the queue is full. That is the most basic form of backpressure. `Queue.shutdown()` in Python 3.13+ gives you a cleaner shutdown path for consumers.</p>

## Design Questions You Must Answer

- do producers wait when the system is full?
- do they fail after a timeout?
- do you drop old work or reject new work?
- how many downstream operations may run concurrently?

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Use bounded queues</h3>
    <p>Bursts should be absorbed, not allowed to grow memory usage without limit.</p>
  </div>
  <div class="check-card">
    <h3>Use semaphores</h3>
    <p>A queue alone does not limit how hard workers hit a downstream API or database.</p>
  </div>
  <div class="check-card">
    <h3>Add timeout policy</h3>
    <p>Decide when enqueue or processing latency becomes failure, not just delay.</p>
  </div>
  <div class="check-card">
    <h3>Pick a drop policy</h3>
    <p>Some real-time systems are better off dropping stale work than trying to process everything eventually.</p>
  </div>
</div>

## Practical Connections

- webhook ingestion
- rate-limited API fan-out
- background worker queues
- burst-heavy internal pipelines

## Official Sources

- [Queues](https://docs.python.org/3/library/asyncio-queue.html)
- [Synchronization Primitives](https://docs.python.org/3/library/asyncio-sync.html)
