# ASGI lifecycle lab: scope, receive, send, lifespan, and HTTP flow.
# ASGI 라이프사이클 실험: scope, receive, send, lifespan, HTTP 흐름.
# Why: FastAPI feels less magical once the raw ASGI message exchange is visible.
# 왜: ASGI 메시지 교환을 직접 보면 FastAPI의 런타임 구조가 훨씬 덜 마법처럼 보인다.
# Use when: learning why ASGI exists and how Uvicorn-style servers call an app.
# 언제 쓰나: ASGI가 왜 생겼는지, Uvicorn 같은 서버가 앱을 어떻게 호출하는지 감을 잡을 때 좋다.

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeAlias

Message: TypeAlias = dict[str, object]
Scope: TypeAlias = dict[str, object]
Receive: TypeAlias = Callable[[], Awaitable[Message]]
Send: TypeAlias = Callable[[Message], Awaitable[None]]


@dataclass(slots=True)
class QueueReceive:
    messages: list[Message]

    async def __call__(self) -> Message:
        if not self.messages:
            raise RuntimeError("receive queue is empty")
        return self.messages.pop(0)


@dataclass(slots=True)
class CollectorSend:
    messages: list[Message] = field(default_factory=list)

    async def __call__(self, message: Message) -> None:
        self.messages.append(message)


async def demo_app(scope: Scope, receive: Receive, send: Send) -> None:
    scope_type_obj = scope.get("type")
    if not isinstance(scope_type_obj, str):
        raise TypeError("scope['type'] must be a string")

    if scope_type_obj == "lifespan":
        while True:
            message = await receive()
            message_type_obj = message.get("type")
            if message_type_obj == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message_type_obj == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
            else:
                raise RuntimeError(f"unexpected lifespan event: {message_type_obj!r}")

    if scope_type_obj != "http":
        raise RuntimeError(f"unsupported scope type: {scope_type_obj}")

    path_obj = scope.get("path", "/")
    if not isinstance(path_obj, str):
        raise TypeError("scope['path'] must be a string")

    body = b""
    while True:
        message = await receive()
        message_type_obj = message.get("type")
        if message_type_obj != "http.request":
            raise RuntimeError(f"unexpected http event: {message_type_obj!r}")

        chunk_obj = message.get("body", b"")
        more_body_obj = message.get("more_body", False)
        if not isinstance(chunk_obj, bytes):
            raise TypeError("http.request body must be bytes")
        if not isinstance(more_body_obj, bool):
            raise TypeError("http.request more_body must be bool")

        body += chunk_obj
        if not more_body_obj:
            break

    # The app emits ASGI response messages instead of returning a response object directly.
    # 앱은 response object를 바로 반환하는 대신 ASGI response message를 보낸다.
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": f"path={path_obj}, body={body.decode('utf-8')}".encode("utf-8"),
        }
    )


async def run_lifespan_lab() -> None:
    receive = QueueReceive(
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
    )
    send = CollectorSend()
    await demo_app({"type": "lifespan"}, receive, send)
    print("lifespan messages:", send.messages)


async def run_http_lab() -> None:
    receive = QueueReceive(
        [
            {
                "type": "http.request",
                "body": b"hello-asgi",
                "more_body": False,
            }
        ]
    )
    send = CollectorSend()
    scope: Scope = {
        "type": "http",
        "method": "POST",
        "path": "/echo",
    }
    await demo_app(scope, receive, send)
    print("http response messages:", send.messages)


async def main() -> None:
    print("== lifespan ==")
    await run_lifespan_lab()
    print("\n== http ==")
    await run_http_lab()


if __name__ == "__main__":
    asyncio.run(main())
