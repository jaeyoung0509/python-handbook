# WebSocket Practical Patterns

<p class="lead">Most WebSocket examples stop at an echo server, but real systems start where that demo ends. Production shapes need auth on connect, room membership, broadcast fan-out, disconnect cleanup, reconnect behavior, and multi-worker boundaries to be designed together. This chapter is about an operationally usable baseline, not a toy route.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: authenticate as early as possible, let a room manager own membership, treat disconnect as normal control flow, and do not hold DB sessions for the lifetime of the socket. In-memory room managers are only safe for a single process. Once you have multiple workers, you usually need Redis pub/sub or another external fan-out layer.</p>
</div>

## The practical shape in one picture

<MermaidDiagram
  caption="A production-minded WebSocket path is a composition of auth, room management, message handling, and external fan-out."
  chart="flowchart LR; A[&quot;Client connects with token&quot;] --> B[&quot;Auth on connect&quot;]; B --> C[&quot;Accept and join room&quot;]; C --> D[&quot;Receive message loop&quot;]; D --> E[&quot;Per-message handler&quot;]; E --> F[&quot;Room manager broadcast&quot;]; F --> G[&quot;Peers in same room&quot;]; F --> H[&quot;Redis pubsub or broker when multi-worker&quot;]; D --> I[&quot;Disconnect cleanup&quot;];"
/>

## 1) Finish authentication at connect time when possible

Common choices:

- query token
- cookie or session
- a short-lived ticket derived from a bearer token
- subprotocol negotiation

Practical rule:

- reject unauthorized clients as early as possible
- do static permission checks at connect time
- keep per-message authorization for room, command, or resource checks that depend on the message itself

```py
from fastapi import WebSocket, status


async def authenticate(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if token != "secret-token":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise RuntimeError("unauthorized websocket")
    return "user-123"
```

## 2) Let a manager own room membership

Fragile shape:

- mutating a global dict ad hoc inside the route
- forgetting cleanup on disconnect
- mixing room state with message-loop logic

Stronger shape:

- a `RoomManager` or `ConnectionHub` owns join, leave, and broadcast
- the route focuses on auth and message-loop orchestration

```py
class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}

    async def join(self, room: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(room, set()).add(websocket)

    def leave(self, room: str, websocket: WebSocket) -> None:
        peers = self.rooms.get(room)
        if peers is None:
            return
        peers.discard(websocket)
        if not peers:
            self.rooms.pop(room, None)
```

## 3) Treat disconnect as normal control flow

Disconnects happen constantly. Tabs close, phones switch networks, proxies time out, and clients reconnect. `WebSocketDisconnect` should usually trigger cleanup, not noisy error handling.

```py
from fastapi import WebSocketDisconnect


try:
    while True:
        text = await websocket.receive_text()
        ...
except WebSocketDisconnect:
    manager.leave(room_id, websocket)
```

## 4) Keep DB sessions short and message-scoped

Why:

- websocket connections may live for a long time
- a connection-wide session increases stale state and resource leakage risk
- many idle sockets can hold unnecessary DB resources if you tie sessions to the whole connection

Practical default:

- short session for connect-time auth if needed
- new short session for message handling when required
- keep broadcast fan-out separate from DB resource ownership

## 5) In-memory broadcast is only safe for single-worker deployments

A room manager implemented as `dict[str, set[WebSocket]]` is simple and fast, but it only sees the connections inside one process.

Once you have multiple workers:

- worker A cannot see worker B's in-memory room state
- clients connected to different workers in the same room will not meet through local broadcast alone

That is where external fan-out layers enter:

- Redis pub/sub
- NATS
- Kafka
- a dedicated realtime gateway

## 6) Reconnect behavior is a joint server/client design problem

Questions that cannot be answered by the server alone:

- does the client use backoff or reconnect too aggressively
- is resume from the last seen event required
- is room rejoin idempotent
- can duplicate delivery be tolerated

Useful defaults:

- exponential backoff
- a session or connection identifier
- offsets, cursors, or last-event IDs if replay matters
- room join that is safe to repeat

## 7) Message shape is part of the contract

In practice, structured envelopes are usually better than raw strings.

```py
from pydantic import BaseModel


class ChatMessage(BaseModel):
    room_id: str
    kind: str
    text: str
```

Why:

- validation is clearer
- room, event type, and payload stay separate
- later protocol versioning is easier

## Recommended baseline

| Concern | Good default | Avoid |
| --- | --- | --- |
| auth | connect-time first-pass auth | accepting first and rejecting late |
| room state | dedicated manager object | ad hoc global dicts in the route |
| disconnect | cleanup path | treating it only as an error |
| DB access | short per-message sessions | one long session per socket |
| multi-worker broadcast | Redis or another external fan-out | expecting in-memory dicts to scale |
| reconnect | backoff and idempotent rejoin | immediate infinite retries |

## Repository examples

- `examples/websocket_auth_and_rooms_lab.py`
- `examples/websocket_redis_pubsub_lab.py`
- `examples/websocket_client_protocol_reconnect_lab.py`
- `examples/fastapi_realtime_and_middleware_lab.py`

## Companion chapters

1. [WebSockets, Streaming, and Middleware](/en/fastapi/websockets-streaming-and-middleware)
2. [Redis Pub/Sub and Multi-worker Broadcast](/en/fastapi/websocket-redis-pubsub)
3. [Client Protocol and Reconnect](/en/fastapi/websocket-client-protocol-and-reconnect)
4. [Proxy, Health, and Shutdown](/en/fastapi/proxy-health-and-shutdown)

## Official References

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI Dependencies in WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette WebSockets](https://www.starlette.io/websockets/)
- [FastAPI Testing WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/)
