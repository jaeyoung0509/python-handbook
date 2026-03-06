# WebSocket client protocol lab: hello, join, event IDs, replay, and reconnect resume.
# WebSocket 클라이언트 프로토콜 실험: hello, join, event id, replay, reconnect resume.
# Why: reconnect stability comes from a protocol contract, not from retrying the socket blindly.
# 왜: reconnect 안정성은 소켓 재시도 자체보다 프로토콜 계약에서 나온다.
# Use when: designing websocket message envelopes, replay policy, and client reconnect behavior.
# 언제 쓰나: websocket 메시지 envelope, replay 정책, client reconnect 동작을 설계할 때 좋다.

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError


class ClientFrame(BaseModel):
    kind: str
    room_id: str | None = None
    text: str | None = None
    resume_from: int | None = None


class ServerFrame(BaseModel):
    kind: str
    protocol_version: int | None = None
    session_id: str | None = None
    room_id: str | None = None
    event_id: int | None = None
    sender: str | None = None
    text: str | None = None


@dataclass(frozen=True, slots=True)
class ChatEvent:
    event_id: int
    room_id: str
    sender: str
    text: str


@dataclass(slots=True)
class ProtocolHub:
    next_event_id: int = 1
    room_events: dict[str, list[ChatEvent]] = field(default_factory=dict)
    room_sockets: dict[str, set[WebSocket]] = field(default_factory=dict)

    def join(self, room_id: str, websocket: WebSocket) -> None:
        self.room_sockets.setdefault(room_id, set()).add(websocket)

    def leave_all(self, websocket: WebSocket) -> None:
        for room_id in list(self.room_sockets):
            peers = self.room_sockets.get(room_id)
            if peers is None:
                continue
            peers.discard(websocket)
            if not peers:
                self.room_sockets.pop(room_id, None)

    def events_after(self, room_id: str, last_seen_id: int) -> list[ChatEvent]:
        return [
            event
            for event in self.room_events.get(room_id, [])
            if event.event_id > last_seen_id
        ]

    def record_event(self, room_id: str, sender: str, text: str) -> ChatEvent:
        event = ChatEvent(
            event_id=self.next_event_id,
            room_id=room_id,
            sender=sender,
            text=text,
        )
        self.next_event_id += 1
        self.room_events.setdefault(room_id, []).append(event)
        return event

    async def broadcast(self, event: ChatEvent) -> None:
        frame = ServerFrame(
            kind="chat.message",
            room_id=event.room_id,
            event_id=event.event_id,
            sender=event.sender,
            text=event.text,
        ).model_dump(exclude_none=True)
        for websocket in list(self.room_sockets.get(event.room_id, set())):
            await websocket.send_json(frame)


TOKENS = {
    "neo-token": "neo",
    "trinity-token": "trinity",
}

hub = ProtocolHub()
app = FastAPI(title="WebSocket Client Protocol Lab")


def reconnect_backoff_seconds(attempt: int, *, base: float = 0.5, cap: float = 4.0) -> float:
    return min(base * (2**attempt), cap)


async def authenticate(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    client_id = TOKENS.get(str(token))
    if client_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    return client_id


@app.websocket("/ws/protocol")
async def protocol_socket(websocket: WebSocket) -> None:
    client_id = await authenticate(websocket)
    if client_id is None:
        return

    await websocket.accept()
    session_id = f"session-{client_id}"
    await websocket.send_json(
        ServerFrame(
            kind="server.hello",
            protocol_version=1,
            session_id=session_id,
        ).model_dump(exclude_none=True)
    )

    try:
        while True:
            raw_frame = await websocket.receive_json()
            try:
                frame = ClientFrame.model_validate(raw_frame)
            except ValidationError:
                await websocket.send_json(
                    ServerFrame(kind="server.error", text="invalid frame").model_dump(exclude_none=True)
                )
                continue

            if frame.kind == "client.join" and frame.room_id is not None:
                hub.join(frame.room_id, websocket)
                await websocket.send_json(
                    ServerFrame(
                        kind="room.joined",
                        room_id=frame.room_id,
                        session_id=session_id,
                    ).model_dump(exclude_none=True)
                )
                resume_from = frame.resume_from or 0
                for event in hub.events_after(frame.room_id, resume_from):
                    await websocket.send_json(
                        ServerFrame(
                            kind="chat.message",
                            room_id=event.room_id,
                            event_id=event.event_id,
                            sender=event.sender,
                            text=event.text,
                        ).model_dump(exclude_none=True)
                    )
                continue

            if frame.kind == "chat.send" and frame.room_id is not None and frame.text is not None:
                event = hub.record_event(frame.room_id, client_id, frame.text)
                await hub.broadcast(event)
                continue

            await websocket.send_json(
                ServerFrame(kind="server.error", text=f"unsupported frame: {frame.kind}").model_dump(
                    exclude_none=True
                )
            )
    except WebSocketDisconnect:
        hub.leave_all(websocket)


def main() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws/protocol?token=neo-token") as neo:
            hello_first = neo.receive_json()
            neo.send_json({"kind": "client.join", "room_id": "core", "resume_from": 0})
            joined_first = neo.receive_json()
            neo.send_json({"kind": "chat.send", "room_id": "core", "text": "first"})
            first_event = neo.receive_json()

        with client.websocket_connect("/ws/protocol?token=trinity-token") as trinity:
            trinity.receive_json()
            trinity.send_json({"kind": "client.join", "room_id": "core", "resume_from": 1})
            joined_trinity = trinity.receive_json()
            trinity.send_json({"kind": "chat.send", "room_id": "core", "text": "while-you-were-away"})
            second_event = trinity.receive_json()

        with client.websocket_connect("/ws/protocol?token=neo-token") as neo_reconnected:
            hello_second = neo_reconnected.receive_json()
            neo_reconnected.send_json({"kind": "client.join", "room_id": "core", "resume_from": 1})
            joined_second = neo_reconnected.receive_json()
            replayed_event = neo_reconnected.receive_json()

    print("hello first:", hello_first)
    print("joined first:", joined_first)
    print("first event:", first_event)
    print("joined trinity:", joined_trinity)
    print("second event:", second_event)
    print("hello second:", hello_second)
    print("joined second:", joined_second)
    print("replayed event:", replayed_event)
    print(
        "reconnect backoff samples:",
        [
            reconnect_backoff_seconds(0),
            reconnect_backoff_seconds(1),
            reconnect_backoff_seconds(2),
            reconnect_backoff_seconds(5),
        ],
    )


if __name__ == "__main__":
    main()
