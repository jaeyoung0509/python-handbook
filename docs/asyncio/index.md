# Asyncio

이 파트는 `async def` 문법이 아니라 "비동기 시스템을 안전하게 운영하는 감각"을 다룬다.

## 이 파트의 목표

- event loop, task, cancellation, TaskGroup을 한 모델로 이해한다.
- backpressure 없는 async 코드를 왜 위험한지 설명할 수 있게 한다.
- FastAPI async endpoint와 DB access의 경계를 이해한다.

## 추천 순서

1. [Event Loop and Tasks](/asyncio/event-loop-and-tasks)
2. [Cancellation and TaskGroup](/asyncio/cancellation-and-taskgroup)
3. [Queues and Backpressure](/asyncio/queues-and-backpressure)
4. [Testing and Debugging](/asyncio/testing-and-debugging)
