# Memory and GC

## 왜 중요한가

Python은 refcount와 cyclic GC를 같이 쓰기 때문에, Go/Java 같은 tracing GC 언어와 메모리 감각이 꽤 다르다.

## 이 장에서 채울 것

- refcount
- cyclic GC
- pymalloc
- object lifetime
- 3.14 incremental cyclic GC 방향

## 실전 연결

- large object graph
- file/socket lifecycle
- memory leak debugging
