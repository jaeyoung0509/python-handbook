# Queues and Backpressure

## 왜 중요한가

async 시스템이 터지는 흔한 이유는 "빨라서"가 아니라 입력을 통제하지 못해서다.

## 이 장에서 채울 것

- `asyncio.Queue`
- producer / consumer
- bounded queue
- semaphore
- backpressure 전략

## 실전 연결

- webhook processing
- API rate limit 대응
- burst traffic handling
