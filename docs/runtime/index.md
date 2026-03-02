# Runtime

이 파트는 CPython을 "언어 실행기"로 읽는 섹션이다.

## 이 파트의 목표

- Python 코드가 실제로 어떻게 실행되는지 감을 만든다.
- object model, bytecode, GIL, GC, subinterpreter를 하나의 그림으로 연결한다.
- 성능/설계 판단이 왜 그렇게 나오는지 이해한다.

## 추천 순서

1. [Execution Model](/runtime/execution-model)
2. [Object Model](/runtime/object-model)
3. [Memory and GC](/runtime/memory-and-gc)
4. [GIL and Subinterpreters](/runtime/gil-and-subinterpreters)
5. [Bytecode and Specialization](/runtime/bytecode-and-specialization)
6. [CPython vs Go Runtime](/cpython-vs-go-runtime)
