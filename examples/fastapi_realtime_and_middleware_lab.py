# FastAPI realtime lab: streaming, SSE, WebSocket, and pure ASGI middleware.
# FastAPI 실시간 실험: streaming, SSE, WebSocket, pure ASGI middleware.
# Why: long-lived connections need a different mental model than ordinary JSON routes.
# 왜: 오래 사는 연결은 일반 JSON route와 다른 정신 모델이 필요하다.
# Use when: learning which transport shape to pick and how middleware sees HTTP vs WebSocket.
# 언제 쓰나: 어떤 transport를 고를지, middleware가 HTTP와 WebSocket을 어떻게 보는지 익힐 때 좋다.

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from starlette.types import ASGIApp, Message, Receive, Scope, Send

SEEN_SCOPES: list[str] = []


class ScopeTagMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type_obj = scope.get("type", "unknown")
        SEEN_SCOPES.append(str(scope_type_obj))

        async def send_wrapper(message: Message) -> None:
            if scope_type_obj == "http" and message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-scope-type", b"http"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


fastapi_app = FastAPI(title="Realtime and Middleware Lab")


async def plain_stream() -> AsyncIterator[bytes]:
    for i in range(3):
        yield f"chunk-{i}\n".encode("utf-8")
        await asyncio.sleep(0.01)


async def sse_stream() -> AsyncIterator[bytes]:
    for i in range(3):
        yield f"data: tick-{i}\n\n".encode("utf-8")
        await asyncio.sleep(0.01)


@fastapi_app.get("/stream")
async def stream_endpoint() -> StreamingResponse:
    return StreamingResponse(plain_stream(), media_type="text/plain")


@fastapi_app.get("/events")
async def events_endpoint() -> StreamingResponse:
    return StreamingResponse(sse_stream(), media_type="text/event-stream")


@fastapi_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"echo:{text}")
    except WebSocketDisconnect:
        return


app: ASGIApp = ScopeTagMiddleware(fastapi_app)


def main() -> None:
    SEEN_SCOPES.clear()
    with TestClient(app) as client:
        stream_response = client.get("/stream")
        events_response = client.get("/events")
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            websocket_reply = websocket.receive_text()

    print("stream media type:", stream_response.headers["content-type"])
    print("stream scope header:", stream_response.headers["x-scope-type"])
    print("stream body:", stream_response.text.strip())
    print("sse media type:", events_response.headers["content-type"])
    print("sse body:", events_response.text.strip())
    print("websocket reply:", websocket_reply)
    print("seen scopes:", SEEN_SCOPES)


if __name__ == "__main__":
    main()
