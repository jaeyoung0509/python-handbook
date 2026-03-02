# Asyncio

<p class="lead">이 파트는 `async def` 문법 설명보다, 실제 서비스에서 비동기 시스템을 안전하게 굴리는 감각을 다룬다. event loop, task, cancellation, timeout, backpressure, debug mode를 한 그림으로 이해해야 FastAPI endpoint, background worker, fan-out 호출, 큐 소비기가 안정적으로 돌아간다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 좋은 asyncio 코드는 "동시에 많이 돌린다"보다 "취소와 정리를 제대로 하고, 입력량을 통제하고, 숨은 blocking I/O를 제거한다"에 가깝다. 구조적 동시성과 backpressure를 모르면 async는 금방 불안정해진다.</p>
</div>

## 이 파트에서 잡아야 할 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>task는 언제 생기나</h3>
    <p>coroutine object와 scheduled task는 다르다. 무엇이 실제로 event loop에 올라갔는지 구분할 수 있어야 한다.</p>
  </div>
  <div class="reading-card">
    <h3>취소는 예외다</h3>
    <p>cancel은 신호가 아니라 `CancelledError` 전파 모델이다. cleanup과 재전파를 이해해야 shutdown이 깨지지 않는다.</p>
  </div>
  <div class="reading-card">
    <h3>백프레셔는 필수다</h3>
    <p>queue maxsize, semaphore, timeout 없이 무한 fan-out을 하면 메모리와 downstream이 먼저 터진다.</p>
  </div>
  <div class="reading-card">
    <h3>테스트는 타이밍 제어다</h3>
    <p>async 버그는 재현보다 관측이 어렵다. timeout, debug mode, task leak 체크가 필요하다.</p>
  </div>
</div>

## 추천 순서

1. [Event Loop and Tasks](/asyncio/event-loop-and-tasks)
2. [Cancellation and TaskGroup](/asyncio/cancellation-and-taskgroup)
3. [Queues and Backpressure](/asyncio/queues-and-backpressure)
4. [Testing and Debugging](/asyncio/testing-and-debugging)

## 실전 규칙

- task를 만들었다면 누가 기다리고 누가 취소하는지 분명해야 한다.
- blocking 함수는 event loop 안에서 직접 호출하지 않는다.
- queue 크기와 동시 실행 수는 항상 제한한다.
- timeout과 cleanup path를 정상 경로만큼 중요하게 다룬다.
