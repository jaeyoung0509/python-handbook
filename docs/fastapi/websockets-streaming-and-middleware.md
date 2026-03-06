# WebSocket, Streaming, Middleware

<p class="lead">FastAPI를 일반 JSON API로만 보면 놓치는 것이 많다. WebSocket, SSE, `StreamingResponse`는 "요청 하나 받고 JSON 하나 돌려주는" 모델보다 연결 수명이 길고, 데이터가 여러 번 흘러가며, middleware와 timeout, shutdown 정책도 다르게 읽어야 한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: `StreamingResponse`는 HTTP 연결 위에서 body를 chunk로 흘려보내고, SSE는 그 위에 `text/event-stream` 규약을 올린 형태이며, WebSocket은 아예 별도 프로토콜 업그레이드와 양방향 메시지 흐름을 가진다. middleware는 이 차이를 존중해야 하고, HTTP 전용인지 pure ASGI인지 의도를 분명히 해야 한다.</p>
</div>

## 세 가지를 같은 표에 두고 본다

| 형태 | 프로토콜 | 연결 수명 | 주로 쓸 때 | 자주 하는 실수 |
| --- | --- | --- | --- | --- |
| 일반 JSON 응답 | HTTP | 짧음 | CRUD, command/query API | route를 비대하게 만듦 |
| `StreamingResponse` | HTTP | 응답 전송 동안 유지 | 큰 파일, 점진적 결과, chunk 전송 | gzip/buffering이 streaming에 미치는 영향 무시 |
| SSE | HTTP + `text/event-stream` | 길 수 있음 | 단방향 서버 push | websocket처럼 양방향이라고 착각 |
| WebSocket | WebSocket | 길고 상태적 | 채팅, 실시간 협업, 양방향 이벤트 | DB session을 연결 전체에 물고 감 |

<MermaidDiagram
  caption="FastAPI에서도 연결 모양에 따라 이벤트 흐름과 운영 포인트가 달라진다."
  chart="flowchart TB; A[&quot;Client&quot;] --> B[&quot;HTTP JSON route&quot;]; A --> C[&quot;HTTP streaming response&quot;]; A --> D[&quot;SSE stream&quot;]; A --> E[&quot;WebSocket connection&quot;]; C --> F[&quot;Chunked body events&quot;]; D --> G[&quot;text/event-stream frames&quot;]; E --> H[&quot;Bidirectional messages&quot;];"
/>

## 1) `StreamingResponse`: 응답 body를 조금씩 보낸다

```py
import asyncio

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def number_stream():
    for i in range(3):
        yield f"{i}\n"
        await asyncio.sleep(0.1)


@app.get("/stream")
async def stream_numbers() -> StreamingResponse:
    return StreamingResponse(number_stream(), media_type="text/plain")
```

언제 좋나:

- 큰 결과를 모두 메모리에 쌓지 않고 보내고 싶을 때
- 생성이 오래 걸리는 결과를 점진적으로 보여주고 싶을 때
- 파일이나 iterator 기반 데이터를 그대로 흘리고 싶을 때

주의:

- streaming 중에는 connection이 열려 있으므로 timeout, client disconnect, backpressure를 같이 봐야 한다.
- Starlette 공식 문서 기준으로 `GZipMiddleware`는 streaming response를 압축할 때 버퍼링할 수 있어 지연이 생길 수 있다.

## 2) SSE: HTTP 기반의 단방향 실시간 push

SSE는 WebSocket보다 단순한 선택지다. 서버에서 클라이언트로만 이벤트를 밀어주고 싶다면 `StreamingResponse`와 `text/event-stream`으로 충분한 경우가 많다.

```py
import asyncio

from fastapi.responses import StreamingResponse


async def event_stream():
    for i in range(3):
        yield f"data: tick-{i}\n\n"
        await asyncio.sleep(0.1)


@app.get("/events")
async def events() -> StreamingResponse:
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

SSE가 잘 맞는 경우:

- 알림 스트림
- 상태 변화 feed
- 한 방향 진행률 업데이트

WebSocket이 더 맞는 경우:

- 클라이언트도 메시지를 보내야 함
- presence, room, subscribe/unsubscribe 같은 상호작용이 많음
- 양방향 프로토콜 설계가 필요함

## 3) WebSocket: 연결 단위 상태와 메시지 흐름을 본다

```py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"echo:{text}")
    except WebSocketDisconnect:
        return
```

여기서 중요한 건 route 함수가 "한 번 실행되고 끝나는 HTTP handler"가 아니라 연결 수명 전체를 소유하는 loop가 된다는 점이다.

실무에서 체크할 것:

- 인증을 연결 직후에 끝낼지, 메시지 단위로 다시 볼지
- 한 연결에 DB session을 오래 들고 있지 않을지
- disconnect를 정상 흐름으로 처리할지
- fan-out과 broadcast를 app 내부에 둘지 별도 infra로 뺄지

## middleware는 "어떤 scope를 다루는가"가 핵심이다

### HTTP 전용 middleware

- request/response 로깅
- 응답 헤더 추가
- CORS, gzip, trusted host, HTTPS redirect

### pure ASGI middleware

- HTTP와 WebSocket을 둘 다 보고 싶을 때
- `scope["type"]`에 따라 분기해야 할 때
- framework request object보다 더 아래층에서 이벤트를 다뤄야 할 때

```py
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class ScopeTagMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_wrapper(message: Message) -> None:
            if scope["type"] == "http" and message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-scope-type", b"http"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

<p class="code-caption">이 형태는 HTTP뿐 아니라 WebSocket scope도 같은 middleware 경계에서 볼 수 있다. "WebSocket까지 포함한 연결 수준 관심사"라면 pure ASGI middleware가 더 자연스럽다.</p>

## middleware와 streaming에서 자주 놓치는 것

- `GZipMiddleware`는 streaming response를 버퍼링할 수 있다.
- SSE는 `text/event-stream`이라 일반 gzip/transform 처리와 다르게 봐야 한다.
- 요청 단위 logger만 보고 있으면 long-lived websocket 연결 비용이 안 보인다.
- WebSocket route 안에서 무거운 blocking 작업을 돌리면 연결 전체가 멈춘다.

## 설계 기준을 짧게 정리하면

| 질문 | 추천 |
| --- | --- |
| 단방향 서버 push면 충분한가 | SSE 우선 검토 |
| 양방향 메시지 흐름이 필요한가 | WebSocket |
| 큰 응답을 점진적으로 보내야 하는가 | `StreamingResponse` |
| HTTP와 WebSocket을 모두 가로채야 하는가 | pure ASGI middleware |
| request당 세션을 websocket 전체에 재사용할 것인가 | 보통 피함 |

## 같이 읽으면 좋은 페이지

1. [ASGI와 Uvicorn](/fastapi/asgi-and-uvicorn)
2. [BackgroundTasks와 오프로딩](/fastapi/background-tasks-and-offloading)
3. [Proxy, Health, Shutdown](/fastapi/proxy-health-and-shutdown)

실행 예제로는 `examples/fastapi_realtime_and_middleware_lab.py`를 같이 보면 streaming, SSE, websocket, pure ASGI middleware가 한 번에 보인다.

## 공식 자료

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI Testing WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/)
- [Starlette Responses](https://www.starlette.io/responses/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
