# BackgroundTasks와 오프로딩

<p class="lead">FastAPI의 `BackgroundTasks`는 편하지만, 이름 때문에 Celery나 워커 큐처럼 오해하기 쉽다. 실제로는 "응답 뒤에 같은 프로세스에서 잠깐 더 할 일"에 가깝다. 이 경계를 모르면 동기 호출을 억지로 `async`로 감싸거나, 반대로 중요한 작업을 메모리 안에만 맡기는 실수를 하게 된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 응답과 트랜잭션 결과에 영향을 주는 일은 route/service 안에서 직접 기다린다. 짧고 best-effort인 후처리는 `BackgroundTasks`에 넣는다. 그리고 retry, durability, CPU-heavy work, 긴 외부 API 호출이 걸린 일은 큐/워커로 뺀다. `BackgroundTasks` 안에서 `def`를 쓸지 `async def`를 쓸지는 "실제 작업이 sync I/O인지, awaitable I/O인지"로 결정한다.</p>
</div>

## 먼저 결론부터: 네 가지 선택지

<MermaidDiagram
  caption="핵심은 '비동기 문법'이 아니라 소유권과 실패 모델이다."
  chart="flowchart TB; A[&quot;작업이 응답 결과를 바꾸는가&quot;] -->|예| B[&quot;route or service에서 직접 await or call&quot;]; A -->|아니오| C[&quot;작업이 짧고 in-process best-effort인가&quot;]; C -->|예, sync I/O| D[&quot;BackgroundTasks + def&quot;]; C -->|예, async I/O| E[&quot;BackgroundTasks + async def&quot;]; C -->|아니오| F[&quot;Queue and worker&quot;];"
/>

## `BackgroundTasks`가 실제로 의미하는 것

- 응답에 붙는 후처리다.
- 같은 프로세스 안에서 실행된다.
- durable queue가 아니다.
- 프로세스가 죽으면 작업도 사라질 수 있다.
- task는 순서대로 실행되고, 하나가 예외를 던지면 뒤 task는 실행되지 않는다.

즉, "메일은 언젠가 꼭 보내져야 한다", "결제 후 반드시 invoice를 생성해야 한다", "실패하면 재시도해야 한다" 같은 요구는 `BackgroundTasks` 단독으로 맡기면 안 된다.

## `def`를 쓸지 `async def`를 쓸지

### `BackgroundTasks` + `def`

언제 좋나:

- 짧은 sync I/O
- 파일 append, audit log, 작은 JSON dump
- 현재 쓰는 라이브러리가 sync API만 제공할 때

왜 괜찮나:

- Starlette는 sync background task를 thread pool에서 실행할 수 있다.
- route 응답 경로를 복잡하게 `async`로 바꾸지 않아도 된다.

주의:

- CPU-heavy 작업은 여기에 넣지 않는다.
- thread pool token은 무한하지 않다.
- sync DB session 같은 request scope 자원을 그대로 넘기지 않는다.

### `BackgroundTasks` + `async def`

언제 좋나:

- 내부가 끝까지 awaitable I/O일 때
- `httpx.AsyncClient`, async Redis client, async broker publish 같은 코드

왜 좋나:

- 이미 async client를 쓰고 있다면 불필요한 thread hop이 없다.
- backpressure와 timeout을 event loop 기준으로 다루기 쉽다.

주의:

- `async def`라고 해서 자동으로 안전하지 않다.
- 내부에서 `time.sleep()`, sync SDK, 무거운 CPU 계산을 돌리면 event loop를 막는다.

## "동기 호출을 background task로 넣어도 되나?"를 판단하는 기준

| 질문 | 그렇다면 | 추천 |
| --- | --- | --- |
| 응답 status나 body가 이 결과에 의존하는가 | 예 | background로 빼지 말고 직접 기다린다 |
| 실패 시 재시도/보장이 필요한가 | 예 | 큐/워커로 뺀다 |
| 작업이 CPU-heavy인가 | 예 | 큐/워커 또는 별도 compute 경로 |
| 작업이 짧은 sync I/O인가 | 예 | `BackgroundTasks` + `def` |
| 작업이 짧은 async I/O인가 | 예 | `BackgroundTasks` + `async def` |

## request scope 자원을 그대로 넘기면 안 되는 이유

FastAPI의 `yield` dependency는 응답 뒤 cleanup된다. 최신 FastAPI 문서 기준으로, 이 cleanup 이후 background task에서 그 리소스를 다시 쓰는 패턴은 권장되지 않는다. 따라서 background task는 request scope session이나 열린 파일 핸들을 잡아 두기보다, 필요한 identifier만 넘기고 자기 안에서 다시 자원을 열어야 한다.

### 나쁜 예

```py
async def create_user(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    user = UserRecord(email="neo@example.com")
    session.add(user)
    await session.commit()

    background_tasks.add_task(send_welcome_email, session, user.id)
    return {"status": "ok"}
```

### 더 안전한 예

```py
async def create_user(
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    user_id = 1
    background_tasks.add_task(send_welcome_email, user_id)
    return {"status": "ok"}
```

```py
async def send_welcome_email(user_id: int) -> None:
    async with AsyncSessionFactory() as session:
        user = await session.get(UserRecord, user_id)
        ...
```

## 어떤 작업을 어디에 둘지 예로 보면

| 작업 | 추천 위치 | 이유 |
| --- | --- | --- |
| 결제 승인 결과 확인 | route/service에서 직접 await | 응답과 일관성에 직접 영향 |
| audit log 한 줄 남기기 | `BackgroundTasks` + `def` | 짧고 best-effort 성격 |
| async webhook 알림 | `BackgroundTasks` + `async def` | 응답 뒤 awaitable I/O |
| PDF 생성, 이미지 리사이즈 | 큐/워커 | CPU 사용량이 크고 재시도 필요 가능 |
| 반드시 전달되어야 하는 이메일 | 큐/워커 | durability와 retry가 중요 |

## 실전에서 자주 하는 실수

- 중요한 작업을 "응답 빠르게 주고 싶다"는 이유로 무조건 background로 밀어 넣는다.
- sync SDK 호출을 `async def` 안에 그대로 넣는다.
- request-scoped session을 background task로 넘긴다.
- background task가 durable queue처럼 retry될 것이라고 기대한다.

## 같이 읽으면 좋은 페이지

1. [ASGI와 Uvicorn](/fastapi/asgi-and-uvicorn)
2. [Lifespan과 테스트](/fastapi/lifespan-and-testing)
3. [Asyncio](/asyncio/)

실행 예제로는 `examples/fastapi_background_tasks_patterns.py`를 같이 보면 sync/async/off-process 판단 기준이 코드로 바로 보인다.

## 공식 자료

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI Dependencies with `yield`](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
- [Starlette Background Tasks](https://www.starlette.io/background/)
- [Starlette Thread Pool](https://www.starlette.io/threadpool/)
