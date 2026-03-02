# Data Model

## 왜 중요한가

Pythonic하다는 말의 절반은 사실 data model을 이해했다는 뜻에 가깝다.

## 이 장에서 채울 것

- object identity / type / value
- attribute access와 method binding
- dunder method가 언어 문법과 연결되는 방식
- `__getattribute__`, `__getattr__`, `__setattr__`의 차이

## 실전 질문

- 왜 `len(obj)`는 `obj.len()`이 아닌가?
- 왜 함수가 클래스에 들어가면 method처럼 보이나?
- 왜 어떤 프레임워크는 필드 선언만 했는데 마법처럼 동작하나?

## 이어서 읽기

- [Descriptors and Properties](/pythonic/descriptors-and-properties)
- [Runtime Object Model](/runtime/object-model)
