# WebSocket auth and rooms lab: auth on connect, room manager, broadcast, disconnect cleanup.
# WebSocket 인증/룸 실험: connect 시 인증, room manager, broadcast, disconnect cleanup.
# Why: realtime code gets fragile fast when auth, room state, and cleanup stay inside one route loop.
# 왜: auth, room 상태, cleanup이 route loop 안에 다 섞이면 realtime 코드가 금방 깨지기 쉽다.
# Use when: learning a practical baseline for FastAPI websocket services before adding Redis or brokers.
# 언제 쓰나: Redis나 broker를 붙이기 전에 FastAPI websocket 서비스의 실전 기본형을 익힐 때 좋다.

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketState


@dataclass(slots=True)
class RoomManager:
    rooms: dict[str, set[WebSocket]] = field(default_factory=dict)

    async def join(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(room_id, set()).add(websocket)

    def leave(self, room_id: str, websocket: WebSocket) -> None:
        peers = self.rooms.get(room_id)
        if peers is None:
            return
        peers.discard(websocket)
        if not peers:
            self.rooms.pop(room_id, None)

    async def broadcast(self, room_id: str, message: str) -> None:
        peers = list(self.rooms.get(room_id, set()))
        for peer in peers:
            if peer.client_state == WebSocketState.CONNECTED:
                await peer.send_text(message)


manager = RoomManager()
app = FastAPI(title="WebSocket Auth and Rooms Lab")


async def authenticate_connection(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if token != "secret-token":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    client_id = websocket.query_params.get("client_id", "anonymous")
    return client_id


@app.websocket("/ws/rooms/{room_id}")
async def room_socket(websocket: WebSocket, room_id: str) -> None:
    client_id = await authenticate_connection(websocket)
    if client_id is None:
        return
    await manager.join(room_id, websocket)
    await manager.broadcast(room_id, f"system:{client_id}:joined")
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast(room_id, f"{client_id}:{text}")
    except WebSocketDisconnect:
        manager.leave(room_id, websocket)


def main() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws/rooms/core?token=secret-token&client_id=neo") as neo:
            first_join = neo.receive_text()
            with client.websocket_connect("/ws/rooms/core?token=secret-token&client_id=trinity") as trinity:
                second_join_for_neo = neo.receive_text()
                second_join_for_trinity = trinity.receive_text()
                neo.send_text("hello-room")
                room_message_for_neo = neo.receive_text()
                room_message_for_trinity = trinity.receive_text()

            remaining_rooms_after_inner_close = sorted(manager.rooms)

        remaining_rooms_after_all_close = sorted(manager.rooms)

        try:
            with client.websocket_connect("/ws/rooms/core?token=bad-token&client_id=smith") as invalid:
                invalid.receive_text()
        except WebSocketDisconnect as exc:
            invalid_close_code = exc.code
        else:
            invalid_close_code = 0

    print("first join message:", first_join)
    print("second join for neo:", second_join_for_neo)
    print("second join for trinity:", second_join_for_trinity)
    print("broadcast for neo:", room_message_for_neo)
    print("broadcast for trinity:", room_message_for_trinity)
    print("rooms after inner close:", remaining_rooms_after_inner_close)
    print("rooms after all close:", remaining_rooms_after_all_close)
    print("invalid token close code:", invalid_close_code)


if __name__ == "__main__":
    main()
