# Performance and Ops

## 왜 중요한가

FastAPI는 빠르지만, 잘못된 I/O 경계나 serialization 비용 때문에 쉽게 느려질 수 있다.

## 이 장에서 채울 것

- async endpoint에서 blocking work 피하기
- validation / serialization cost
- DB connection pool
- worker model
- observability and tracing
