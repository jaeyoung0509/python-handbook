# Cancellation and TaskGroup

## 왜 중요한가

실무 async 코드의 품질은 취소와 정리 cleanup을 얼마나 제대로 다루느냐에서 갈린다.

## 이 장에서 채울 것

- cancellation propagation
- `CancelledError`
- timeout
- `TaskGroup`
- `ExceptionGroup`

## 실전 연결

- API fan-out
- graceful shutdown
- background worker stop sequence
