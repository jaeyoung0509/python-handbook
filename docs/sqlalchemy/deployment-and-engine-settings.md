# 배포별 Engine 설정

<p class="lead">SQLAlchemy 설정은 "좋아 보이는 값 몇 개"를 외우는 문제가 아니다. Lambda, Kubernetes, batch worker, long-lived API server는 process lifetime, connection budget, shutdown 방식이 다르기 때문에 같은 `engine`/`pool` 설정을 그대로 복붙하면 장애가 난다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 먼저 "프로세스가 얼마나 오래 사는가", "동시에 몇 개가 뜰 수 있는가", "이미 외부 connection pooler가 있는가"를 계산하고, 그 다음에 `QueuePool`인지 `NullPool`인지, `pool_size`와 `max_overflow`를 얼마나 줄지 정해야 한다.</p>
</div>

## 먼저 계산해야 할 3가지

1. 프로세스가 long-lived인가, invocation/job 단위로 짧게 끝나는가
2. 동시에 떠 있을 수 있는 process/worker/replica 수가 얼마인가
3. DB 앞에 이미 RDS Proxy, PgBouncer 같은 외부 pooler가 있는가

## 연결 수는 이렇게 계산한다

```text
최대 연결 수 상한 ~= replicas * workers_per_pod * (pool_size + max_overflow)
```

<p class="code-caption">이 계산은 sync API 서버에서 특히 중요하다. pod 6개, worker 2개, `pool_size=10`, `max_overflow=10`이면 이론상 240개 연결까지 튈 수 있다. DB 인스턴스 허용치보다 큰데도 app 쪽 config만 보고 있으면 장애를 늦게 본다.</p>

## 핵심 설정 값의 의미

| 설정 | 무엇을 바꾸나 | 보통 언제 중요해지나 |
| --- | --- | --- |
| `poolclass` | 풀 전략 자체를 바꾼다 | `QueuePool` vs `NullPool` 선택 |
| `pool_size` | 유지할 기본 연결 수 | long-lived API 서버 |
| `max_overflow` | 기본 풀을 넘는 임시 연결 수 | burst traffic이 있는 API 서버 |
| `pool_timeout` | 풀에서 연결을 기다리는 시간 | saturation을 빨리 감지하고 싶을 때 |
| `pool_pre_ping` | checkout 시 연결 생존 확인 | idle disconnect가 잦은 환경 |
| `pool_recycle` | 일정 시간이 지난 연결을 재생성 | DB/server idle timeout이 있는 환경 |
| `pool_use_lifo` | 최근 연결 재사용 선호 | idle connection 수를 줄이고 싶을 때 |
| `autoflush=False` | 숨은 flush를 줄인다 | 서비스/리포지토리 경계를 명시하고 싶을 때 |
| `expire_on_commit=False` | commit 후 객체 접근을 덜 놀랍게 만든다 | API DTO 조립, 로깅 |
| `echo` | SQL 로그 출력 | 로컬 디버깅 전용 |

## 배포 환경별 추천 프로필

| 환경 | 추천 풀 전략 | 세션 scope | 핵심 포인트 |
| --- | --- | --- | --- |
| Lambda에서 DB 직접 연결 | `NullPool` | invocation마다 새 세션 | 함수 컨테이너 재사용은 있어도 대규모 동시성은 여러 execution environment로 퍼진다 |
| Lambda + RDS Proxy/PgBouncer | `NullPool` 또는 아주 작은 풀 | invocation마다 새 세션 | 외부 pooler가 있으면 앱 쪽 pooling은 작게 가져가라 |
| Kubernetes sync API | `QueuePool` | request마다 새 세션 | `pool_size`, `max_overflow`, worker 수를 connection budget에 맞춰 계산 |
| Kubernetes async API | async engine + 적당한 풀 | request마다 새 `AsyncSession` | `AsyncSession`을 task 간 공유하지 말고 shutdown 시 dispose |
| batch/CLI/worker | `NullPool` 또는 아주 작은 풀 | job마다 새 세션 | 길지 않은 작업이면 대개 큰 풀이 이득이 없다 |

## Lambda에서의 기준

### 왜 보통 `NullPool`이 먼저 나오나

- Lambda는 요청마다 짧은 실행 단위를 반복한다.
- concurrency가 늘면 한 프로세스 안 풀이 커지는 게 아니라 execution environment 자체가 여러 개 생긴다.
- 그래서 앱 안에 큰 풀을 두는 것보다, invocation마다 짧은 세션을 열고 닫는 쪽이 더 읽기 쉽고 안전한 경우가 많다.

### 기본 예시

```py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def handler(event, context):
    session = SessionFactory()
    try:
        ...
    finally:
        session.close()
```

<p class="code-caption">Lambda에서는 engine 자체는 handler 밖에서 초기화해 재사용하고, session은 invocation마다 새로 만든다. AWS 공식 가이드는 execution environment 재사용을 위해 SDK client와 DB connection initialization을 handler 밖에 두라고 권장한다.</p>

### Lambda + RDS Proxy일 때

- RDS Proxy나 PgBouncer를 이미 두었다면 앱 안 `QueuePool`을 크게 키울 이유가 줄어든다.
- 보통은 `NullPool` 또는 매우 작은 앱 측 풀로 시작하는 편이 안전하다.
- 핵심은 "이중 pooling"으로 연결 수 계산을 흐리게 만들지 않는 것이다.

## Kubernetes에서의 기준

FastAPI 공식 배포 가이드는 Kubernetes 같은 클러스터 환경에서는 한 컨테이너당 한 Uvicorn 프로세스로 단순하게 가는 방식을 권장한다. 이 접근은 DB connection math를 계산하기도 쉽다.

### sync API 서버 기본 예시

```py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_timeout=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_use_lifo=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)
```

### 왜 이 값들이 자주 나오나

- `pool_pre_ping=True`: 오래 idle된 connection이 죽었을 때 request 초반에 빠르게 감지
- `pool_recycle=1800`: DB/server idle timeout보다 약간 짧게 잡아 stale connection을 줄임
- `pool_timeout=5`: 풀 고갈이 나면 무한 대기 대신 빨리 실패해 문제를 드러냄
- `pool_use_lifo=True`: 항상 모든 connection을 뜨겁게 유지하기보다 최근 연결 재사용을 선호

### worker 수와 같이 봐야 한다

- pod 1개에 worker 1개면 계산이 단순하다.
- pod 1개에 worker 4개면 engine pool도 사실상 4세트 생긴다.
- 그래서 `replicas * workers * (pool_size + max_overflow)`를 먼저 계산해야 한다.

## async 서비스 기준

```py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_timeout=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_use_lifo=True,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)
```

- async라고 해서 세션을 공유해도 되는 게 아니다.
- request마다 새 `AsyncSession`을 만들고, concurrent task 간 공유하지 않는다.
- 앱 shutdown 시 `await engine.dispose()`를 호출해 연결 정리를 명시하는 편이 좋다.

## batch, CLI, worker 기준

- job 하나가 짧게 끝나면 `NullPool`이 더 단순하다.
- 오래 도는 worker라도 동시에 DB를 세게 치지 않으면 큰 풀은 과한 경우가 많다.
- 작업이 끝날 때 `engine.dispose()`를 호출하면 연결 정리가 더 분명해진다.

## 실전에서 하지 않는 편이 좋은 것

- Lambda와 Kubernetes에 같은 pool 설정을 그대로 쓰는 것
- 외부 pooler가 있는데 앱 쪽 `pool_size`도 크게 잡는 것
- `max_overflow`를 크게 두고 총 연결 수 계산을 안 하는 것
- 세션을 request 바깥에 오래 들고 가는 것
- `AsyncSession` 하나를 여러 task가 동시에 쓰게 하는 것
- 로컬에서 잘 되던 `echo=True`를 운영에 남겨두는 것

## 이 저장소의 실행 예제

배포 프로필별 권장 설정은 `examples/sqlalchemy_deployment_profiles.py` 에 runnable note 형태로 넣어두었다.

## 같이 읽으면 좋은 페이지

- [Session and Unit of Work](/sqlalchemy/session-and-unit-of-work)
- [Async SQLAlchemy](/sqlalchemy/async-sqlalchemy)
- [Performance and Ops](/fastapi/performance-and-ops)

## 공식 자료

- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Using AWS Lambda with Amazon RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/)
