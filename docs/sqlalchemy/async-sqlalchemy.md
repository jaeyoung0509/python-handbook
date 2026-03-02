# Async SQLAlchemy

## 왜 중요한가

async를 붙였다고 DB access가 자동으로 좋아지진 않는다. connection, session, transaction 경계는 더 엄격하게 봐야 한다.

## 이 장에서 채울 것

- async engine / session
- async transaction scope
- FastAPI integration pattern
- sync API와의 차이

## 실전 질문

- 언제 async DB가 진짜 이득인가?
- sync session을 threadpool로 감싸는 것과 무엇이 다른가?
