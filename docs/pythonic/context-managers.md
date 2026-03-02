# Context Managers

## 왜 중요한가

Python에서 자원 관리와 경계(boundary)를 가장 Pythonic하게 표현하는 도구가 context manager다.

## 이 장에서 채울 것

- `with` 문이 실제로 하는 일
- `__enter__`, `__exit__`
- `contextlib`
- async context manager
- transaction / lifespan / resource scope 패턴

## 실전 연결

- DB session scope
- FastAPI lifespan
- 테스트 fixture와 cleanup
