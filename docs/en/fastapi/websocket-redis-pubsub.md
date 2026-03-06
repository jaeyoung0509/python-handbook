# Redis Pub/Sub and Multi-worker Broadcast

<p class="lead">Starting with an in-memory room manager is fine. The problem appears when you have more than one worker. Clients connected to the same room on different workers can no longer see each other through local memory alone. This chapter explains why Redis pub/sub becomes useful, where it belongs in the architecture, and where its guarantees stop.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: with one worker, in-memory room broadcast is enough. With multiple workers, each worker still needs its own local room manager, but it also needs an external fan-out layer. Redis pub/sub is a common default for that. However, Redis pub/sub does not provide replay or acknowledgements, so if missed messages matter, you likely need Streams or another durable log.</p>
</div>

## Why a local room manager stops being enough

<MermaidDiagram
  caption="In a single worker, room state lives in one memory space. In multiple workers, room state is split across processes."
  chart="flowchart LR; A[&quot;Client A&quot;] --> B[&quot;Worker 1 room manager&quot;]; C[&quot;Client B&quot;] --> D[&quot;Worker 2 room manager&quot;]; B --> E[&quot;Local broadcast only&quot;]; D --> E; B --> F[&quot;Redis pubsub channel&quot;]; D --> F;"
/>

- worker 1 memory is not shared with worker 2
- `dict[str, set[WebSocket]]` only knows the sockets connected to one process
- a multi-worker room needs an external message layer to fan events out across workers

## Where Redis pub/sub sits

The common shape is:

1. each worker owns its local `RoomManager`
2. when a client message arrives, the worker publishes an event to a Redis channel
3. all workers subscribe to the relevant room channels
4. each worker fans the event out to its own local peers

Redis does not own the sockets. It acts as the cross-worker broadcast bus.

## Minimal code shape

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

Workers also need a subscribe loop.

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

## Channel naming is part of the design

Good defaults:

- include environment prefixes such as `env:service:room:{room_id}`
- include tenant prefixes when tenants share infrastructure
- define an escaping or normalization rule for room IDs

Why:

- staging and production should not collide on the same Redis
- multi-tenant room namespaces need clear separation

## Publish payloads as envelopes

An envelope is usually better than an ad hoc string.

```py
from pydantic import BaseModel


class PubSubEnvelope(BaseModel):
    room_id: str
    sender: str
    text: str
    event_id: int
```

Benefits:

- worker-to-worker message shape stays stable
- protocol versioning or trace IDs can be added later
- replay and dead-letter extensions are easier

## Know Redis pub/sub limits clearly

Redis pub/sub is lightweight and fast, but its guarantee model is intentionally weak.

| Requirement | Redis pub/sub | Stronger alternative |
| --- | --- | --- |
| cross-worker fan-out | good fit | - |
| replay after temporary disconnect | weak | Redis Streams, Kafka |
| acknowledgements and retries | weak | durable queue or log |
| event history lookup | none | Streams, append log, DB log |

So Redis pub/sub is a good fit when you only need to fan out to currently connected sockets. It is not sufficient by itself when reconnecting clients must catch up on missed events.

## Own the broker connection in lifespan

- create and close the Redis client in app lifespan
- start worker subscription tasks at startup
- cancel them during shutdown
- let the worker-side subscription loop own reconnect and backoff behavior

## Recommended baseline

| Concern | Recommended default |
| --- | --- |
| single-worker fan-out | in-memory room manager |
| multi-worker fan-out | local room manager plus Redis pub/sub |
| replay requirements | keep an event log or Streams separately |
| Redis namespace | include env or service or tenant prefixes |
| Redis connection lifetime | app lifespan ownership |

## Repository examples

- `examples/websocket_redis_pubsub_lab.py`
- `examples/websocket_auth_and_rooms_lab.py`

## Companion chapters

1. [WebSocket Practical Patterns](/en/fastapi/websocket-practical-patterns)
2. [Client Protocol and Reconnect](/en/fastapi/websocket-client-protocol-and-reconnect)
3. [Proxy, Health, and Shutdown](/en/fastapi/proxy-health-and-shutdown)

## Official References

- [Redis Pub/Sub](https://redis.io/docs/latest/develop/pubsub/)
- [Redis asyncio Examples](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
