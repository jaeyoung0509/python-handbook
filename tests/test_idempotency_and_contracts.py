from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from hypothesis import given
from hypothesis import strategies as st


def payload_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class StoredResponse:
    fingerprint: str
    body: dict[str, Any]


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self.records: dict[str, StoredResponse] = {}

    def execute(
        self,
        *,
        key: str,
        payload: dict[str, Any],
        operation: Callable[[], dict[str, Any]],
    ) -> tuple[dict[str, Any], bool]:
        fingerprint = payload_fingerprint(payload)
        existing = self.records.get(key)
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise ValueError("key conflict")
            return existing.body, True

        result = operation()
        self.records[key] = StoredResponse(fingerprint=fingerprint, body=result)
        return result, False


@given(
    key=st.text(
        min_size=1,
        max_size=12,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
    ),
    customer_id=st.text(
        min_size=1,
        max_size=12,
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
    ),
    amount=st.integers(min_value=1, max_value=10_000),
)
def test_same_key_same_payload_runs_once(
    key: str,
    customer_id: str,
    amount: int,
) -> None:
    store = InMemoryIdempotencyStore()
    call_count = 0

    def operation() -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        return {"status": "created", "customer_id": customer_id, "amount": amount}

    payload = {"customer_id": customer_id, "amount": amount}
    first_result, first_cached = store.execute(key=key, payload=payload, operation=operation)
    second_result, second_cached = store.execute(key=key, payload=payload, operation=operation)

    assert first_cached is False
    assert second_cached is True
    assert first_result == second_result
    assert call_count == 1


def test_same_key_different_payload_conflicts() -> None:
    store = InMemoryIdempotencyStore()

    first_payload = {"customer_id": "neo", "amount": 100}
    second_payload = {"customer_id": "neo", "amount": 999}

    store.execute(
        key="order-001",
        payload=first_payload,
        operation=lambda: {"status": "created"},
    )

    try:
        store.execute(
            key="order-001",
            payload=second_payload,
            operation=lambda: {"status": "created"},
        )
    except ValueError as error:
        assert str(error) == "key conflict"
    else:
        raise AssertionError("expected a key conflict")


def test_asgi_transport_contract() -> None:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async def run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    asyncio.run(run())
