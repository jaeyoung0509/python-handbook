# Idempotency와 Outbox

<p class="lead">실서비스에서는 "한 번만 실행된다"는 보장이 생각보다 자주 깨진다. 클라이언트 retry, proxy retry, worker 재시작, 네트워크 timeout, duplicate event delivery 때문에 create API와 publish path는 중복 실행을 전제로 설계하는 편이 맞다. 여기서 핵심이 idempotency key와 transactional outbox다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: idempotency는 "같은 요청을 두 번 받아도 결과가 하나처럼 보이게" 만드는 전략이고, outbox는 "DB write와 event publish를 같은 트랜잭션 경계에 묶는" 전략이다. 둘은 retry-heavy 서비스에서 같이 등장하는 경우가 많다.</p>
</div>

<MermaidDiagram
  caption="중복 실행과 메시지 유실을 따로 다루지 않으면 API와 비동기 처리 사이가 쉽게 어긋난다."
  chart="flowchart LR; A[&quot;client request with idempotency key&quot;] --> B[&quot;use case&quot;]; B --> C[&quot;domain write&quot;]; C --> D[&quot;store idempotency record&quot;]; C --> E[&quot;store outbox message&quot;]; D --> F[&quot;commit&quot;]; E --> F; F --> G[&quot;outbox publisher&quot;];"
/>

## 1) idempotency는 왜 필요한가

아래 상황은 모두 흔하다.

- 클라이언트가 timeout 때문에 같은 POST를 재전송한다.
- reverse proxy 또는 API gateway가 retry한다.
- 앱은 성공했는데 응답이 끊겨 클라이언트는 실패로 본다.
- queue consumer가 at-least-once delivery로 같은 메시지를 다시 받는다.

즉, 중복 실행을 예외로 보면 안 된다.

## 2) idempotency key의 기본 계약

좋은 idempotency 계약은 보통 아래와 같다.

- 같은 key + 같은 payload: 기존 결과를 재사용한다.
- 같은 key + 다른 payload: `409 Conflict` 또는 유사한 에러로 거부한다.
- key 저장소에는 요청 fingerprint와 응답 snapshot을 함께 둔다.

### 이 계약이 중요한 이유

key만 보고 무조건 기존 응답을 돌려주면, 다른 payload가 우연히 같은 key를 썼을 때 잘못된 결과를 주게 된다.

## 3) key 저장소는 무엇을 기억해야 하나

최소한 아래 정도는 자주 필요하다.

- idempotency key
- request fingerprint
- 처리 결과 snapshot
- 상태(`in_progress`, `completed`, `failed`)
- TTL 또는 보존 기간

`in_progress` 상태를 두면 동시 중복 요청 처리도 더 안정적으로 만들 수 있다.

## 4) outbox는 왜 필요한가

다음 코드는 위험하다.

1. DB에 주문 저장
2. commit
3. 브로커에 `order.created` 발행

이 순서에서 2와 3 사이에 프로세스가 죽으면, DB에는 주문이 있는데 이벤트는 안 나간다.

반대로 이벤트를 먼저 발행하고 commit이 실패해도 문제다.

outbox pattern은 도메인 write와 "보낼 메시지"를 같은 DB transaction 안에 함께 저장한다. 그 다음 별도 publisher가 outbox row를 읽어 실제 broker publish를 수행한다.

## 5) UoW와 outbox를 같이 두는 구조

```py
class UnitOfWork(abc.ABC):
    orders: OrdersRepository
    idempotency: IdempotencyRepository
    outbox: OutboxRepository

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError
```

```py
def handle(command: CreateOrderCommand, uow: UnitOfWork) -> dict[str, str]:
    existing = uow.idempotency.get(command.idempotency_key, command.payload_fingerprint)
    if existing is not None:
        return existing

    order = Order.create(...)
    uow.orders.add(order)
    uow.outbox.add(OutboxMessage.from_domain_event(order.pull_events()[0]))

    result = {"order_id": order.id, "status": "created"}
    uow.idempotency.save(command.idempotency_key, command.payload_fingerprint, result)
    uow.commit()
    return result
```

핵심은 commit 전까지 domain row, outbox row, idempotency row가 같은 transaction 안에 있다는 점이다.

## 6) `BackgroundTasks`로 대체하면 왜 부족한가

`BackgroundTasks`는 in-process 후처리다.

- 프로세스가 죽으면 사라질 수 있다.
- retry/durability가 없다.
- DB write와 atomic하게 묶이지 않는다.

즉, "꼭 보내야 하는 이벤트"나 "반드시 한 번만 처리되어야 하는 create action"을 `BackgroundTasks`만으로 해결하려 하면 빈틈이 생긴다.

## 7) 동시성까지 보면 설계가 더 중요해진다

### API idempotency

- 같은 key로 동시에 두 요청이 들어올 수 있다.
- unique constraint 또는 `INSERT ... ON CONFLICT` 같은 DB 전략이 필요할 수 있다.

### outbox publish

- publisher가 여러 worker면 같은 outbox row를 중복 집어갈 수 있다.
- status transition, leasing, `FOR UPDATE SKIP LOCKED` 같은 전략이 필요할 수 있다.

즉, idempotency와 outbox는 "개념만 있으면 끝"이 아니라 저장소 원자성과 worker coordination까지 봐야 한다.

## 8) 어디서부터 시작하면 좋나

### 작은 서비스

- API create path에 idempotency key 도입
- outbox table + 단일 publisher worker
- 실패한 publish row는 재시도 대상 표시

### 커지는 서비스

- status / retry_count / next_attempt_at / last_error 같은 outbox metadata
- dedupe key와 payload fingerprint 명확화
- metrics: duplicate hit rate, outbox lag, retry rate

## 9) 하지 않는 편이 좋은 것

- same key + different payload를 그냥 기존 응답으로 처리한다.
- 이벤트 publish를 commit 뒤 best-effort 함수 호출로 끝낸다.
- at-least-once consumer에 dedupe 전략이 없다.
- outbox를 두고도 publish worker가 idempotent하지 않다.

## 10) 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>idempotency key와 payload fingerprint를 같이 저장하는가</h3>
    <p>같은 key를 다른 요청이 재사용하는 충돌을 구분해야 한다.</p>
  </div>
  <div class="check-card">
    <h3>도메인 write와 outbox write가 같은 transaction인가</h3>
    <p>이 둘이 분리되면 publish 누락 또는 phantom event가 생길 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>publisher retry와 dedupe 이야기가 있는가</h3>
    <p>outbox를 넣어도 consumer/publisher idempotency가 없으면 중복 문제는 남는다.</p>
  </div>
  <div class="check-card">
    <h3>metrics를 볼 수 있는가</h3>
    <p>duplicate hit rate와 outbox lag은 운영에서 반드시 봐야 한다.</p>
  </div>
</div>

## 이 저장소에서 같이 보면 좋은 문서

1. [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)
2. [BackgroundTasks와 오프로딩](/fastapi/background-tasks-and-offloading)
3. [Session과 Unit of Work](/sqlalchemy/session-and-unit-of-work)
4. [계약 진화와 지속가능한 CD](/playbooks/contract-evolution-and-sustainable-cd)

실행 예제는 `examples/idempotency_outbox_lab.py`, 테스트 예제는 `tests/test_idempotency_and_contracts.py`를 보면 된다.

## 참고 자료

- [The Idempotency-Key HTTP Header Field](https://www.ietf.org/archive/id/draft-ietf-httpapi-idempotency-key-header-07.html)
- [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
