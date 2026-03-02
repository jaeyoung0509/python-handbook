# Dependency Injection

## 왜 중요한가

FastAPI의 DI는 편하지만, 너무 쉽게 전역 상태와 request state를 섞게 만들 수도 있다.

## 이 장에서 채울 것

- `Depends`
- dependency graph
- yield dependency
- request scoped resource
- test override

## 실전 연결

- DB session 제공
- auth principal 주입
- external client lifecycle 관리
