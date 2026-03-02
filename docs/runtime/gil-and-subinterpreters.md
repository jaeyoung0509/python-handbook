# GIL and Subinterpreters

## 왜 중요한가

이 주제는 Python의 병렬성 논쟁 거의 전부와 연결된다.

## 이 장에서 채울 것

- GIL이 정확히 제한하는 것
- I/O bound vs CPU bound
- per-interpreter GIL
- free-threaded build
- subinterpreter model

## 실전 연결

- thread를 써도 되는 경우
- process가 더 나은 경우
- 3.14 `InterpreterPoolExecutor`를 어디까지 기대해도 되는지
