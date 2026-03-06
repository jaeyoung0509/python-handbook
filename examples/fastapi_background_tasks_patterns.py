# FastAPI background task patterns: inline vs background sync vs background async vs queue worker.
# FastAPI 백그라운드 작업 패턴: inline, background sync, background async, queue worker 비교.
# Why: async syntax and background execution are different decisions, and mixing them causes reliability bugs.
# 왜: async 문법과 background 실행은 다른 결정인데, 둘을 섞어 생각하면 신뢰성 버그가 생긴다.
# Use when: deciding whether a task should run inline, in BackgroundTasks, or in an external worker.
# 언제 쓰나: 작업을 inline으로 실행할지, BackgroundTasks에 둘지, 외부 워커로 뺄지 판단할 때 좋다.

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import StrEnum

from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

EVENTS: list[str] = []


class ExecutionMode(StrEnum):
    INLINE = "inline-await"
    BACKGROUND_SYNC = "background-sync"
    BACKGROUND_ASYNC = "background-async"
    QUEUE_WORKER = "queue-worker"


@dataclass(frozen=True, slots=True)
class TaskProfile:
    name: str
    affects_response: bool
    requires_delivery_guarantee: bool
    cpu_heavy: bool
    async_io: bool


def choose_execution_mode(profile: TaskProfile) -> ExecutionMode:
    if profile.affects_response:
        return ExecutionMode.INLINE
    if profile.requires_delivery_guarantee or profile.cpu_heavy:
        return ExecutionMode.QUEUE_WORKER
    if profile.async_io:
        return ExecutionMode.BACKGROUND_ASYNC
    return ExecutionMode.BACKGROUND_SYNC


def write_audit_log(email: str) -> None:
    # Short sync I/O fits a sync background task well enough.
    # 짧은 sync I/O는 sync background task에 두기 적합하다.
    time.sleep(0.01)
    EVENTS.append(f"sync-audit:{email}")


async def send_webhook(email: str) -> None:
    # Real async I/O should stay async instead of pretending to be sync.
    # 진짜 async I/O라면 억지로 sync로 바꾸지 말고 async로 유지한다.
    await asyncio.sleep(0.01)
    EVENTS.append(f"async-webhook:{email}")


AUDIT_PROFILE = TaskProfile(
    name="audit-log",
    affects_response=False,
    requires_delivery_guarantee=False,
    cpu_heavy=False,
    async_io=False,
)

WEBHOOK_PROFILE = TaskProfile(
    name="webhook",
    affects_response=False,
    requires_delivery_guarantee=False,
    cpu_heavy=False,
    async_io=True,
)

INVOICE_PROFILE = TaskProfile(
    name="invoice-pdf",
    affects_response=False,
    requires_delivery_guarantee=True,
    cpu_heavy=True,
    async_io=False,
)

PAYMENT_PROFILE = TaskProfile(
    name="payment-authorization",
    affects_response=True,
    requires_delivery_guarantee=True,
    cpu_heavy=False,
    async_io=True,
)

app = FastAPI(title="Background Task Patterns Lab")


@app.post("/audit")
def create_audit(background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(write_audit_log, "neo@example.com")
    return {"mode": choose_execution_mode(AUDIT_PROFILE).value}


@app.post("/webhook")
async def trigger_webhook(background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(send_webhook, "neo@example.com")
    return {"mode": choose_execution_mode(WEBHOOK_PROFILE).value}


@app.post("/invoice")
def create_invoice() -> dict[str, str]:
    # Durable, retryable, or CPU-heavy work should move to a queue worker.
    # 내구성/재시도/CPU 부담이 큰 일은 queue worker로 빼야 한다.
    return {
        "mode": choose_execution_mode(INVOICE_PROFILE).value,
        "reason": "move this job to an external worker",
    }


@app.post("/payment")
async def authorize_payment() -> dict[str, str]:
    # If the result changes the response, do it inline and await it here.
    # 결과가 응답을 바꾸면 background로 미루지 말고 여기서 직접 기다린다.
    await asyncio.sleep(0.01)
    return {"mode": choose_execution_mode(PAYMENT_PROFILE).value}


def run_http_lab() -> None:
    EVENTS.clear()
    with TestClient(app) as client:
        audit_response = client.post("/audit")
        webhook_response = client.post("/webhook")
        invoice_response = client.post("/invoice")
        payment_response = client.post("/payment")

    print("audit endpoint:", audit_response.json())
    print("webhook endpoint:", webhook_response.json())
    print("invoice endpoint:", invoice_response.json())
    print("payment endpoint:", payment_response.json())
    print("completed background events:", EVENTS)


def print_decision_table() -> None:
    profiles = [
        AUDIT_PROFILE,
        WEBHOOK_PROFILE,
        INVOICE_PROFILE,
        PAYMENT_PROFILE,
    ]
    for profile in profiles:
        print(profile.name, "->", choose_execution_mode(profile).value)


def main() -> None:
    print("== decision table ==")
    print_decision_table()
    print("\n== app exercise ==")
    run_http_lab()


if __name__ == "__main__":
    main()
