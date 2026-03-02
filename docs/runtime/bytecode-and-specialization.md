# Bytecode and Specialization

## 왜 중요한가

Python 3.11 이후 성능을 이야기할 때는 적응형 특수화를 빼고 말하기 어렵다.

## 이 장에서 채울 것

- bytecode 읽는 법
- `dis` 사용법
- adaptive interpreter
- specialization이 잘 일어나는 코드와 아닌 코드
- JIT가 여기에 어떻게 이어지는지

## 실전 연결

- hot path profiling
- Python loop 최적화 감각
- function call / attribute lookup cost 감각
