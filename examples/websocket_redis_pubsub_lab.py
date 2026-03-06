# WebSocket Redis pub/sub lab: local-only rooms vs broker-backed multi-worker fan-out.
# WebSocket Redis pub/sub 실험: local-only room과 broker-backed multi-worker fan-out 비교.
# Why: in-memory room broadcast stops at one worker, and the failure mode is easy to miss in local dev.
# 왜: in-memory room broadcast는 worker 하나에서만 통하고, 로컬 개발에서는 그 한계가 잘 안 보인다.
# Use when: learning why Redis pub/sub appears once websocket traffic spans multiple workers.
# 언제 쓰나: websocket 트래픽이 여러 worker로 퍼질 때 왜 Redis pub/sub이 필요한지 익힐 때 좋다.

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from pydantic import BaseModel
from redis.asyncio import Redis
from redis.asyncio.client import PubSub


class PubSubEnvelope(BaseModel):
    room_id: str
    sender: str
    text: str
    event_id: int


Subscriber = Callable[[PubSubEnvelope], Awaitable[None]]


class Broker(ABC):
    @abstractmethod
    async def publish(self, envelope: PubSubEnvelope) -> None: ...

    @abstractmethod
    async def subscribe(self, room_id: str, subscriber: Subscriber) -> None: ...


@dataclass(slots=True)
class InMemoryBroker(Broker):
    subscribers: dict[str, list[Subscriber]] = field(default_factory=dict)

    async def publish(self, envelope: PubSubEnvelope) -> None:
        for subscriber in list(self.subscribers.get(envelope.room_id, [])):
            await subscriber(envelope)

    async def subscribe(self, room_id: str, subscriber: Subscriber) -> None:
        self.subscribers.setdefault(room_id, []).append(subscriber)


class RedisPubSubBroker(Broker):
    def __init__(self, redis: Redis, *, prefix: str = "ws") -> None:
        self.redis = redis
        self.prefix = prefix

    def channel_for(self, room_id: str) -> str:
        return f"{self.prefix}:room:{room_id}"

    async def publish(self, envelope: PubSubEnvelope) -> None:
        await self.redis.publish(
            self.channel_for(envelope.room_id),
            envelope.model_dump_json(),
        )

    async def subscribe(self, room_id: str, subscriber: Subscriber) -> None:
        pubsub = self.redis.pubsub()
        channel = self.channel_for(room_id)
        await pubsub.subscribe(channel)
        asyncio.create_task(self._pump(pubsub, subscriber))

    async def _pump(self, pubsub: PubSub, subscriber: Subscriber) -> None:
        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None:
                    await asyncio.sleep(0.01)
                    continue
                data_obj = message.get("data")
                if isinstance(data_obj, bytes):
                    payload = data_obj.decode("utf-8")
                else:
                    payload = str(data_obj)
                await subscriber(PubSubEnvelope.model_validate_json(payload))
        finally:
            await pubsub.aclose()


@dataclass(slots=True)
class FakeSocket:
    client_id: str
    inbox: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LocalOnlyWorker:
    name: str
    rooms: dict[str, list[FakeSocket]] = field(default_factory=dict)

    def connect(self, room_id: str, client_id: str) -> FakeSocket:
        socket = FakeSocket(client_id=client_id)
        self.rooms.setdefault(room_id, []).append(socket)
        return socket

    async def send_chat(self, room_id: str, sender: str, text: str) -> None:
        for socket in self.rooms.get(room_id, []):
            socket.inbox.append(f"{self.name}:{sender}:{text}")


@dataclass(slots=True)
class BrokerBackedWorker:
    name: str
    broker: Broker
    next_event_id: int = 1
    rooms: dict[str, list[FakeSocket]] = field(default_factory=dict)
    subscribed_rooms: set[str] = field(default_factory=set)

    async def connect(self, room_id: str, client_id: str) -> FakeSocket:
        socket = FakeSocket(client_id=client_id)
        self.rooms.setdefault(room_id, []).append(socket)
        if room_id not in self.subscribed_rooms:
            await self.broker.subscribe(room_id, self._handle_broker_event)
            self.subscribed_rooms.add(room_id)
        return socket

    async def _handle_broker_event(self, envelope: PubSubEnvelope) -> None:
        for socket in self.rooms.get(envelope.room_id, []):
            socket.inbox.append(f"{self.name}:{envelope.sender}:{envelope.text}")

    async def send_chat(self, room_id: str, sender: str, text: str) -> None:
        envelope = PubSubEnvelope(
            room_id=room_id,
            sender=sender,
            text=text,
            event_id=self.next_event_id,
        )
        self.next_event_id += 1
        await self.broker.publish(envelope)


async def local_only_demo() -> tuple[list[str], list[str]]:
    worker_a = LocalOnlyWorker("worker-a")
    worker_b = LocalOnlyWorker("worker-b")
    neo = worker_a.connect("core", "neo")
    trinity = worker_b.connect("core", "trinity")
    await worker_a.send_chat("core", "neo", "hello-without-broker")
    return neo.inbox, trinity.inbox


async def broker_demo() -> tuple[list[str], list[str]]:
    broker = InMemoryBroker()
    worker_a = BrokerBackedWorker("worker-a", broker)
    worker_b = BrokerBackedWorker("worker-b", broker)
    neo = await worker_a.connect("core", "neo")
    trinity = await worker_b.connect("core", "trinity")
    await worker_a.send_chat("core", "neo", "hello-with-broker")
    return neo.inbox, trinity.inbox


async def main() -> None:
    local_neo, local_trinity = await local_only_demo()
    broker_neo, broker_trinity = await broker_demo()

    print("local-only neo inbox:", local_neo)
    print("local-only trinity inbox:", local_trinity)
    print("broker neo inbox:", broker_neo)
    print("broker trinity inbox:", broker_trinity)
    print("redis adapter note:", RedisPubSubBroker.__name__, "uses redis.asyncio.Redis in production")


if __name__ == "__main__":
    asyncio.run(main())
