# SQLAlchemy deployment profiles for Lambda, Kubernetes, and jobs.
# Lambda, Kubernetes, job 환경을 위한 SQLAlchemy 배포 프로필 예제.
# Why: engine and pool settings must follow the runtime's process model and connection budget.
# 왜: engine과 pool 설정은 런타임의 프로세스 모델과 연결 예산을 따라가야 한다.
# Use when: comparing deployment targets before choosing pool settings for a new service.
# 언제 쓰나: 새 서비스를 배포하기 전에 환경별 pool 설정 기준을 비교하고 싶을 때 쓴다.

from __future__ import annotations

from dataclasses import dataclass
from pprint import pprint
from typing import Any

from sqlalchemy.pool import NullPool, QueuePool


@dataclass(frozen=True, slots=True)
class DeploymentProfile:
    name: str
    engine_kwargs: dict[str, Any]
    session_kwargs: dict[str, Any]
    notes: tuple[str, ...]


def lambda_direct_profile() -> DeploymentProfile:
    return DeploymentProfile(
        name="lambda_direct_db",
        engine_kwargs={
            "poolclass": NullPool,
        },
        session_kwargs={
            "autoflush": False,
            "expire_on_commit": False,
        },
        notes=(
            "Create the engine outside the Lambda handler.",
            "Open one short-lived Session per invocation.",
            "Prefer RDS Proxy when concurrency grows.",
        ),
    )


def lambda_proxy_profile() -> DeploymentProfile:
    return DeploymentProfile(
        name="lambda_with_rds_proxy",
        engine_kwargs={
            "poolclass": NullPool,
        },
        session_kwargs={
            "autoflush": False,
            "expire_on_commit": False,
        },
        notes=(
            "Let the proxy own most of the pooling story.",
            "Avoid large application-side pools on top of the proxy.",
            "One invocation should still own one short-lived Session.",
        ),
    )


def kubernetes_sync_profile() -> DeploymentProfile:
    return DeploymentProfile(
        name="kubernetes_sync_api",
        engine_kwargs={
            "poolclass": QueuePool,
            "pool_size": 5,
            "max_overflow": 5,
            "pool_timeout": 5,
            "pool_pre_ping": True,
            "pool_recycle": 1800,
            "pool_use_lifo": True,
        },
        session_kwargs={
            "autoflush": False,
            "expire_on_commit": False,
        },
        notes=(
            "Multiply pool settings by replicas and worker count.",
            "Prefer one process per container in Kubernetes for simpler math.",
            "Dispose the engine during shutdown.",
        ),
    )


def kubernetes_async_profile() -> DeploymentProfile:
    return DeploymentProfile(
        name="kubernetes_async_api",
        engine_kwargs={
            "pool_size": 10,
            "max_overflow": 10,
            "pool_timeout": 5,
            "pool_pre_ping": True,
            "pool_recycle": 1800,
            "pool_use_lifo": True,
        },
        session_kwargs={
            "autoflush": False,
            "expire_on_commit": False,
        },
        notes=(
            "Create one AsyncSession per request.",
            "Async engines use an async-adapted queue-style pool under the hood.",
            "Do not share one AsyncSession across concurrent tasks.",
            "Await engine.dispose() during shutdown.",
        ),
    )


def batch_worker_profile() -> DeploymentProfile:
    return DeploymentProfile(
        name="batch_or_worker",
        engine_kwargs={
            "poolclass": NullPool,
        },
        session_kwargs={
            "autoflush": False,
            "expire_on_commit": False,
        },
        notes=(
            "Short jobs rarely benefit from a large in-process pool.",
            "Dispose the engine when the job ends.",
        ),
    )


def max_connection_budget(
    *,
    replicas: int,
    workers_per_replica: int,
    pool_size: int,
    max_overflow: int,
) -> int:
    return replicas * workers_per_replica * (pool_size + max_overflow)


def normalize_engine_kwargs(engine_kwargs: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in engine_kwargs.items():
        if isinstance(value, type):
            normalized[key] = value.__name__
        else:
            normalized[key] = value
    return normalized


def main() -> None:
    profiles = [
        lambda_direct_profile(),
        lambda_proxy_profile(),
        kubernetes_sync_profile(),
        kubernetes_async_profile(),
        batch_worker_profile(),
    ]

    for profile in profiles:
        print(f"\n[{profile.name}]")
        print("engine kwargs:")
        pprint(normalize_engine_kwargs(profile.engine_kwargs))
        print("session kwargs:")
        pprint(profile.session_kwargs)
        print("notes:")
        for note in profile.notes:
            print(f"- {note}")

    print("\n[kubernetes connection budget example]")
    print(
        max_connection_budget(
            replicas=6,
            workers_per_replica=2,
            pool_size=5,
            max_overflow=5,
        )
    )


if __name__ == "__main__":
    main()
