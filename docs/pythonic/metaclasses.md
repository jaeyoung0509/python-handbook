# Metaclasses

## 왜 중요한가

metaclass는 Python에서 가장 과장되게 소비되지만, 동시에 framework internals를 이해할 때는 꼭 필요한 개념이다.

## 이 장에서 채울 것

- class body 실행 시점
- class object 생성 과정
- metaclass가 개입하는 지점
- `__new__`, `__init_subclass__`, class decorator 비교
- metaclass를 써야 하는 경우와 쓰면 안 되는 경우

## 실전 연결

- declarative class registration
- plugin registry
- DSL-like class definition

## 먼저 읽어야 하는 것

- [Data Model](/pythonic/data-model)
- [Descriptors and Properties](/pythonic/descriptors-and-properties)
