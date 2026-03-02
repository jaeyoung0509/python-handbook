# Event Loop and Tasks

## 왜 중요한가

`async/await`는 문법이 아니라 스케줄링 계약이다. 이 감각이 없으면 비동기 코드는 금방 불안정해진다.

## 이 장에서 채울 것

- event loop
- coroutine vs task
- scheduling point
- blocking call이 끼치는 영향
- `create_task()`를 언제 직접 써도 되는가
