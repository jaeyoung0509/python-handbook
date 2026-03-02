# Modern asyncio: structured concurrency, bounded queues, cancellation, and timeout.
# 현대 asyncio: 구조적 동시성, bounded queue, cancellation, timeout.
# Why: async systems fail more often from poor shutdown and missing backpressure than from syntax mistakes.
# 왜: async 시스템은 문법 실수보다 shutdown/cancellation/backpressure 설계 미흡 때문에 더 자주 깨진다.
# Use when: building workers, fan-out jobs, API integrations, or backpressure-aware pipelines.
# 언제 쓰나: worker, fan-out 작업, 외부 API 연동, backpressure 있는 파이프라인에 좋다.

from __future__ import annotations

import asyncio


async def producer(queue: asyncio.Queue[int]) -> None:
    for item in range(6):
        print("produce", item, "qsize before:", queue.qsize())
        await queue.put(item)
        print("enqueued", item, "qsize after:", queue.qsize())
        await asyncio.sleep(0.02)


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
    except asyncio.CancelledError:
        # Cleanup belongs in the cancellation path as much as the success path.
        # cleanup은 성공 경로만큼 취소 경로에서도 중요하다.
        print(name, "cancelled")
        raise


async def run_pipeline() -> None:
    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=2)
    limiter = asyncio.Semaphore(2)

    async with asyncio.TaskGroup() as task_group:
        producer_task = task_group.create_task(producer(queue))
        for index in range(3):
            task_group.create_task(worker(f"worker-{index}", queue, limiter))

        await producer_task
        await queue.join()
        queue.shutdown()


async def main() -> None:
    try:
        async with asyncio.timeout(3.0):
            await run_pipeline()
    except TimeoutError:
        print("pipeline timed out")


if __name__ == "__main__":
    asyncio.run(main())
