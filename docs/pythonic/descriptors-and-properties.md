# Descriptors and Properties

## 왜 중요한가

descriptor는 Python framework를 이해하는 핵심 장치다. ORM field, validation field, computed attribute 대부분이 여기로 연결된다.

## 이 장에서 채울 것

- data descriptor vs non-data descriptor
- `property`가 사실상 descriptor라는 점
- attribute lookup order
- method binding과 function descriptor

## 실전 연결

- SQLAlchemy instrumented attribute
- Pydantic field metadata 접근
- custom validation/computed attribute 설계

## 이어서 읽기

- [Decorators](/pythonic/decorators)
- [Metaclasses](/pythonic/metaclasses)
