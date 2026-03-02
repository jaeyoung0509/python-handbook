# Object Model

## 왜 중요한가

CPython은 거의 모든 값을 객체로 다룬다. 이 비용 구조를 이해해야 Pythonic 설계와 성능 판단이 동시에 선다.

## 이 장에서 채울 것

- object header 감각
- type object와 method slot
- attribute lookup
- bound method
- mutability와 identity

## 실전 연결

- attribute-heavy domain model
- `__slots__`를 언제 고려할지
- method dispatch cost 감각
