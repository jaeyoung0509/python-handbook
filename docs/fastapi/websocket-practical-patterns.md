# WebSocket 실전 패턴

<p class="lead">WebSocket 예제는 보통 echo server에서 끝나지만, 실서비스는 거기서부터 시작이다. 실제로는 connect 시 인증, room membership, broadcast fan-out, disconnect cleanup, reconnect 전략, multi-worker 경계가 한 세트로 따라온다. 이 페이지는 "돌아가는 demo"가 아니라 운영 가능한 기본 모양을 정리한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 인증은 가능하면 connect 시점에 끝내고, room membership은 별도 객체가 소유하며, disconnect는 예외가 아니라 정상 제어 흐름으로 다룬다. in-memory room manager는 single-process까지만 안전하고, worker가 둘 이상이면 Redis pub/sub 같은 외부 fan-out 계층이 필요하다. DB session은 연결 전체에 물고 가지 말고 메시지 처리 단위로 짧게 연다.</p>
</div>

## 실전 구조를 한 그림으로 보면

<MermaidDiagram
  caption="운영 가능한 WebSocket 기본 구조는 route 하나가 아니라 auth, room manager, message handler, external fan-out의 조합이다."
  chart="flowchart LR; A[&quot;Client connects with token&quot;] --> B[&quot;Auth on connect&quot;]; B --> C[&quot;Accept and join room&quot;]; C --> D[&quot;Receive message loop&quot;]; D --> E[&quot;Per-message handler&quot;]; E --> F[&quot;Room manager broadcast&quot;]; F --> G[&quot;Peers in same room&quot;]; F --> H[&quot;Redis pubsub or broker when multi-worker&quot;]; D --> I[&quot;Disconnect cleanup&quot;];"
/>

## 1) 인증은 connect 직후에 끝내는 편이 좋다

가장 흔한 선택지:

- query token
- cookie / session
- bearer token에서 파생한 short-lived ticket
- subprotocol negotiation

실무 기준:

- 인증 실패는 가능한 빨리 connection을 거부한다.
- connect 시 확인할 수 있는 정적 권한은 여기서 끝낸다.
- 메시지별 권한은 room, command, resource 기준으로 추가 검증한다.

```py
from fastapi import WebSocket, status


async def authenticate(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if token != "secret-token":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise RuntimeError("unauthorized websocket")
    return "user-123"
```

## 2) room membership은 route가 아니라 manager가 소유한다

나쁜 패턴:

- route 함수 안 전역 dict를 즉흥적으로 만지기
- disconnect 시 cleanup 누락
- room state와 broadcast 로직이 handler loop 안에 섞이기

더 나은 패턴:

- `RoomManager`나 `ConnectionHub`가 join/leave/broadcast 책임을 가진다.
- route는 auth와 message loop orchestration에 집중한다.

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

## 3) disconnect는 예외가 아니라 정상 흐름이다

WebSocket에서는 disconnect가 자주 일어난다. 네트워크 변화, 탭 종료, 모바일 전환, 프록시 타임아웃 전부 disconnect를 만든다. 따라서 `WebSocketDisconnect`는 오류 로그를 잔뜩 찍을 사건이 아니라 cleanup 트리거로 보는 편이 맞다.

```py
from fastapi import WebSocketDisconnect


try:
    while True:
        text = await websocket.receive_text()
        ...
except WebSocketDisconnect:
    manager.leave(room_id, websocket)
```

## 4) DB session은 연결 전체가 아니라 메시지 단위로 짧게 연다

왜냐하면:

- 연결은 길게 살 수 있다.
- 연결 전체에 session을 물고 있으면 stale state와 누수 위험이 커진다.
- idle websocket 수가 많아지면 쓸데없이 DB 자원을 오래 잡을 수 있다.

실무 기준:

- connect 시 인증/권한 확인용 짧은 session
- 메시지 처리 시 필요하면 새 session
- broadcast fan-out은 DB session과 분리

## 5) in-memory broadcast는 single-worker까지만 안전하다

`dict[str, set[WebSocket]]` 기반 room manager는 간단하고 빠르지만, 프로세스가 하나일 때만 전체 연결을 알고 있다.

multi-worker가 되면:

- worker A의 메모리는 worker B와 공유되지 않는다.
- 같은 room에 들어와도 서로 다른 worker에 붙으면 local broadcast로는 못 만난다.

그래서 worker가 둘 이상이면 보통:

- Redis pub/sub
- NATS
- Kafka
- dedicated realtime gateway

같은 외부 fan-out 계층이 필요하다.

## 6) 재연결 전략은 서버/클라이언트가 같이 설계해야 한다

서버만 보고 끝내면 안 되는 포인트:

- 클라이언트가 backoff 없이 재연결 폭주하지 않는가
- 마지막 이벤트 이후 resume가 필요한가
- room rejoin이 idempotent한가
- duplicate delivery를 감당할 수 있는가

실무 기본선:

- exponential backoff
- session or connection id
- replay가 필요하면 offset / cursor / last event id
- room join은 여러 번 와도 안전하게 처리

## 7) 메시지 shape도 계약이다

실전에서는 단순 문자열보다 envelope 형태가 보통 낫다.

```py
from pydantic import BaseModel


class ChatMessage(BaseModel):
    room_id: str
    kind: str
    text: str
```

이유:

- validation이 쉬워진다.
- room, event type, payload를 분리할 수 있다.
- 추후 protocol versioning에 유리하다.

## 추천 기본 패턴

| 관심사 | 추천 기본값 | 피할 것 |
| --- | --- | --- |
| auth | connect 시 1차 인증 | accept 후 뒤늦게 거부 |
| room state | manager 객체로 분리 | route 안 전역 dict 남발 |
| disconnect | cleanup 정상 흐름 | 에러로만 취급 |
| DB access | 메시지 단위 짧은 session | 연결 전체 session 고정 |
| multi-worker broadcast | Redis 등 외부 fan-out | in-memory dict로 확장 기대 |
| reconnect | backoff + idempotent rejoin | 즉시 무한 재시도 |

## 이 저장소 예제

- `examples/websocket_auth_and_rooms_lab.py`
- `examples/websocket_redis_pubsub_lab.py`
- `examples/websocket_client_protocol_reconnect_lab.py`
- `examples/fastapi_realtime_and_middleware_lab.py`

## 같이 읽으면 좋은 페이지

1. [WebSocket, Streaming, Middleware](/fastapi/websockets-streaming-and-middleware)
2. [Redis Pub/Sub과 Multi-worker Broadcast](/fastapi/websocket-redis-pubsub)
3. [Client Protocol과 Reconnect](/fastapi/websocket-client-protocol-and-reconnect)
4. [Proxy, Health, Shutdown](/fastapi/proxy-health-and-shutdown)

## 공식 자료

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI Dependencies in WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette WebSockets](https://www.starlette.io/websockets/)
- [FastAPI Testing WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/)
