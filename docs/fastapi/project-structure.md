# Project Structure

## 왜 중요한가

FastAPI는 빠르게 시작하기 쉽지만, 구조를 잘못 잡으면 route 파일에 모든 책임이 몰린다.

## 이 장에서 채울 것

- app / router / service / repository / schema 분리
- startup code와 import side effect
- settings 관리
- domain layer와 framework layer 분리

## 실전 질문

- 어디까지 FastAPI 의존성을 안쪽 레이어에 넣어도 되는가?
- schema와 ORM model을 같은 타입으로 써도 되는가?
