# Redis Pub/Sub과 Multi-worker Broadcast

<p class="lead">WebSocket room manager를 in-memory dict로 시작하는 것은 괜찮다. 문제는 worker가 2개가 되는 순간부터 생긴다. 같은 room에 있어도 서로 다른 worker에 붙은 클라이언트는 서로를 볼 수 없기 때문이다. 이 장은 왜 Redis pub/sub이 필요한지, 어디에 두어야 하는지, 또 어디까지가 pub/sub의 한계인지 정리한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: worker가 하나면 in-memory room broadcast로 충분하다. worker가 여러 개면 각 worker의 local room manager와 별도로 외부 fan-out 계층이 필요하고, Redis pub/sub은 그 기본 선택지다. 다만 Redis pub/sub은 replay나 ack를 보장하지 않으므로 "놓친 메시지를 다시 받아야 하는가"가 중요하면 Streams나 다른 durable broker를 검토해야 한다.</p>
</div>

## 왜 local room manager만으로는 안 되는가

<MermaidDiagram
  caption="single-worker에서는 room state가 한 메모리에 있지만, multi-worker에서는 room state가 worker마다 갈라진다."
  chart="flowchart LR; A[&quot;Client A&quot;] --> B[&quot;Worker 1 room manager&quot;]; C[&quot;Client B&quot;] --> D[&quot;Worker 2 room manager&quot;]; B --> E[&quot;Local broadcast only&quot;]; D --> E; B --> F[&quot;Redis pubsub channel&quot;]; D --> F;"
/>

- worker 1의 메모리는 worker 2와 공유되지 않는다.
- 따라서 `dict[str, set[WebSocket]]`는 "해당 worker 안에서만" room 전체를 알고 있다.
- multi-worker에서 전체 room fan-out을 만들려면, worker들 사이를 잇는 외부 메시지 계층이 필요하다.

## Redis pub/sub을 어디에 두는가

보통 구조는 이렇다.

1. 각 worker는 자기 로컬 `RoomManager`를 가진다.
2. 클라이언트 메시지가 들어오면 worker는 local peer에 직접 보내지 않고 Redis channel에 publish한다.
3. 모든 worker는 해당 room channel을 subscribe하고 있다.
4. 받은 이벤트를 자기 worker에 붙은 local peer들에게 fan-out한다.

즉, Redis는 socket을 직접 다루지 않고 "worker 간 fan-out 버스" 역할만 한다.

## 최소 코드 모양

```py
from redis.asyncio import Redis


class RedisPubSubBroker:
    def __init__(self, redis: Redis, *, prefix: str = "ws") -> None:
        self.redis = redis
        self.prefix = prefix

    def channel_for(self, room_id: str) -> str:
        return f"{self.prefix}:room:{room_id}"

    async def publish(self, room_id: str, payload: str) -> None:
        await self.redis.publish(self.channel_for(room_id), payload)
```

worker 쪽에서는 subscribe loop가 필요하다.

```py
pubsub = redis.pubsub()
await pubsub.subscribe("ws:room:core")

while True:
    message = await pubsub.get_message(
        ignore_subscribe_messages=True,
        timeout=1.0,
    )
    if message is None:
        continue
    ...
```

## channel naming도 설계다

좋은 기본 규칙:

- `env:service:room:{room_id}`처럼 environment prefix를 둔다
- tenant가 섞이면 tenant prefix도 둔다
- room id를 그대로 쓰기보다 escape 규칙을 둔다

이유:

- staging과 production이 같은 Redis를 쓸 때 충돌을 피한다.
- 멀티테넌트 시스템에서 room namespace를 분리한다.

## publish payload는 envelope로 고정한다

문자열 한 줄보다 envelope가 낫다.

```py
from pydantic import BaseModel


class PubSubEnvelope(BaseModel):
    room_id: str
    sender: str
    text: str
    event_id: int
```

장점:

- worker 간 메시지 shape가 안정적이다.
- 추후 protocol version이나 trace id를 넣기 쉽다.
- replay나 dead-letter로 확장할 때도 덜 아프다.

## Redis pub/sub의 한계를 명확히 알아야 한다

Redis pub/sub은 가볍고 빠르지만, 운영 모델이 단순한 대신 보장도 약하다.

| 요구사항 | Redis pub/sub | 더 강한 대안 |
| --- | --- | --- |
| worker 간 fan-out | 잘 맞음 | - |
| subscriber가 잠깐 끊겨도 replay 필요 | 약함 | Redis Streams, Kafka |
| ack/retry 필요 | 약함 | durable queue or log |
| event history 조회 | 없음 | Streams, DB append log |

따라서 "현재 붙어 있는 websocket들에게만 fan-out"이면 pub/sub이 잘 맞고, "나중에 reconnect한 클라이언트도 중간 메시지를 받아야 함"까지 들어오면 pub/sub만으로는 부족할 수 있다.

## lifespan에서 broker 연결을 소유한다

- Redis client는 app lifespan에서 열고 닫는 편이 가장 읽기 쉽다.
- subscribe task는 worker startup 시 올리고, shutdown에서 취소한다.
- reconnect와 backoff도 worker 내부 subscription loop가 소유하는 편이 낫다.

## 추천 기본 패턴

| 관심사 | 추천 |
| --- | --- |
| single-worker fan-out | in-memory room manager |
| multi-worker fan-out | local room manager + Redis pub/sub |
| replay가 필요한가 | event log/Streams를 따로 둔다 |
| Redis namespace | env/service/tenant prefix 포함 |
| Redis 연결 수명 | lifespan 소유 |

## 이 저장소 예제

- `examples/websocket_redis_pubsub_lab.py`
- `examples/websocket_auth_and_rooms_lab.py`

## 같이 읽으면 좋은 페이지

1. [WebSocket 실전 패턴](/fastapi/websocket-practical-patterns)
2. [Client Protocol과 Reconnect](/fastapi/websocket-client-protocol-and-reconnect)
3. [Proxy, Health, Shutdown](/fastapi/proxy-health-and-shutdown)

## 공식 자료

- [Redis Pub/Sub](https://redis.io/docs/latest/develop/pubsub/)
- [Redis asyncio Examples](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
