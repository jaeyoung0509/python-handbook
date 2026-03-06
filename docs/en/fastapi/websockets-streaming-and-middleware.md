# WebSockets, Streaming, and Middleware

<p class="lead">If you only view FastAPI as a JSON API framework, you miss an important part of the runtime model. WebSockets, SSE, and `StreamingResponse` all have longer-lived connection behavior, incremental data flow, and different middleware, timeout, and shutdown concerns than a one-shot JSON response.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: `StreamingResponse` keeps HTTP but streams the body in chunks. SSE builds a `text/event-stream` convention on top of HTTP for one-way server push. WebSocket upgrades to a separate bidirectional protocol. Middleware should respect those differences, and you should be explicit about whether it is HTTP-only or pure ASGI.</p>
</div>

## Put the three shapes on one table

| Shape | Protocol | Connection lifetime | Good fit | Common mistake |
| --- | --- | --- | --- | --- |
| regular JSON response | HTTP | short | CRUD, query, command APIs | overgrowing the route layer |
| `StreamingResponse` | HTTP | open while body is sent | large output, incremental results, chunked transfer | ignoring buffering or gzip impact |
| SSE | HTTP plus `text/event-stream` | potentially long | one-way notifications and progress feeds | treating it like bidirectional websocket traffic |
| WebSocket | WebSocket | long and stateful | chat, collaboration, bidirectional event flows | holding a DB session for the whole connection |

<MermaidDiagram
  caption="Even in FastAPI, each connection shape implies a different event and operational model."
  chart="flowchart TB; A[&quot;Client&quot;] --> B[&quot;HTTP JSON route&quot;]; A --> C[&quot;HTTP streaming response&quot;]; A --> D[&quot;SSE stream&quot;]; A --> E[&quot;WebSocket connection&quot;]; C --> F[&quot;Chunked body events&quot;]; D --> G[&quot;text-event-stream frames&quot;]; E --> H[&quot;Bidirectional messages&quot;];"
/>

## 1) `StreamingResponse`: send the body incrementally

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

It fits well when:

- you do not want to buffer all output in memory first
- partial results should appear progressively
- you want to stream from an iterator or file-like source

Watch out for:

- open connections make timeouts, client disconnects, and backpressure more important
- Starlette's docs note that `GZipMiddleware` may buffer streaming responses before compressing them, which can add delay

## 2) SSE: one-way real-time push over HTTP

SSE is often the simpler option when only the server needs to push events to the client. In many cases, `StreamingResponse` plus `text/event-stream` is enough.

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

SSE is a good fit for:

- notification streams
- state feeds
- one-way progress updates

WebSocket is a better fit when:

- the client also needs to send messages
- rooms, presence, subscribe or unsubscribe flows matter
- the protocol is truly bidirectional and stateful

## 3) WebSocket: reason about connection lifetime and message flow

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

The important shift is that this is no longer a one-shot HTTP handler. The route owns the connection lifecycle and a message loop.

Things to decide explicitly:

- whether auth is done once at connect time or rechecked per message
- whether DB resources are reopened per operation instead of held for the entire connection
- whether disconnect is treated as normal control flow
- whether fan-out and broadcast stay in-process or move to dedicated infrastructure

## Middleware is really about which scopes you need to touch

### HTTP-oriented middleware

- request and response logging
- response header injection
- CORS, gzip, trusted host, HTTPS redirect

### Pure ASGI middleware

- when both HTTP and WebSocket scopes matter
- when you need to branch on `scope["type"]`
- when the concern sits below framework request objects

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

<p class="code-caption">This shape can observe both HTTP and WebSocket scopes at the same boundary. If the concern is really connection-level, pure ASGI middleware is usually the cleaner model.</p>

## Things people miss around middleware and streaming

- `GZipMiddleware` may buffer streaming responses
- SSE uses `text/event-stream` and should not be treated like an ordinary text response
- request-only logging often hides the cost of long-lived websocket connections
- blocking work inside a websocket loop can stall the connection badly

## Short design guide

| Question | Recommendation |
| --- | --- |
| Is one-way server push enough? | try SSE first |
| Do you need bidirectional messaging? | use WebSocket |
| Do you need to send large or incremental output? | use `StreamingResponse` |
| Must middleware observe both HTTP and WebSocket? | use pure ASGI middleware |
| Should a request-scoped session live across the whole websocket? | usually no |

## Companion chapters

1. [ASGI and Uvicorn](/en/fastapi/asgi-and-uvicorn)
2. [Background Tasks and Offloading](/en/fastapi/background-tasks-and-offloading)
3. [Proxy, Health, and Shutdown](/en/fastapi/proxy-health-and-shutdown)

For runnable examples, pair this chapter with `examples/fastapi_realtime_and_middleware_lab.py`.

## Official References

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI Testing WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/)
- [Starlette Responses](https://www.starlette.io/responses/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
