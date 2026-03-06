# ASGI와 Uvicorn

<p class="lead">FastAPI를 잘 쓰려면 route 함수 문법보다 먼저 FastAPI가 어떤 런타임 위에서 도는지 알아야 한다. FastAPI는 server가 아니라 ASGI app이고, Uvicorn은 그 앱을 실제 소켓/HTTP/WebSocket 세계와 연결해 주는 ASGI server다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Uvicorn은 연결을 받아 event loop를 돌리고, HTTP/WebSocket을 파싱해 ASGI `scope`, `receive`, `send` 인터페이스로 앱을 호출한다. FastAPI/Starlette는 그 위에서 routing, dependency injection, validation, response serialization을 담당한다. 이 구분이 보여야 worker, timeout, proxy, lifespan 문제를 풀 수 있다.</p>
</div>

## 요청 하나가 지나가는 전체 경로

<MermaidDiagram
  caption="FastAPI 요청 경로는 route 함수에서 시작하지 않는다. 소켓, ASGI server, middleware, dependency, response message가 한 흐름으로 이어진다."
  chart="flowchart LR; A[&quot;Socket accepted by Uvicorn&quot;] --> B[&quot;HTTP or WebSocket parser&quot;]; B --> C[&quot;ASGI scope and receive events&quot;]; C --> D[&quot;Starlette middleware stack&quot;]; D --> E[&quot;FastAPI routing and dependencies&quot;]; E --> F[&quot;Response or websocket messages&quot;]; F --> G[&quot;Uvicorn writes bytes to client&quot;];"
/>

## FastAPI와 Uvicorn의 책임을 분리해서 본다

| 주체 | 주된 책임 | 여기서 생기는 질문 |
| --- | --- | --- |
| Uvicorn | 소켓 수락, 이벤트 루프, 프로토콜 파싱, connection timeout, worker 프로세스 | keep-alive, graceful shutdown, proxy header, concurrency limit |
| ASGI contract | `scope`, `receive`, `send`, `http`/`websocket`/`lifespan` | 요청이 아니라 어떤 이벤트 흐름이 오가는가 |
| Starlette/FastAPI | middleware, routing, dependency, validation, serialization, exception handling | route가 얼마나 얇아야 하나, resource lifecycle을 어디에 두나 |

## ASGI 최소 형태를 먼저 본다

```py
async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    message = await receive()
    assert message["type"] == "http.request"

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
            "body": b"hello from ASGI",
        }
    )
```

<p class="code-caption">핵심은 함수가 request object를 바로 받는 것이 아니라 `scope`, `receive`, `send`라는 더 일반적인 프로토콜 인터페이스를 받는다는 점이다. FastAPI는 이 위에서 request object와 dependency system을 만들어준다.</p>

## Uvicorn이 실제로 하는 일

### 1. connection을 받아 ASGI 앱을 호출한다

- TCP connection과 HTTP/WebSocket 프로토콜 처리를 맡는다.
- 파싱된 정보를 ASGI `scope`와 이벤트로 바꾼다.
- 앱이 `send()`로 보낸 응답 메시지를 다시 네트워크 바이트로 쓴다.

### 2. lifespan을 서버 차원에서 조율한다

- startup 시 app lifespan을 열고
- shutdown 시 app lifespan을 닫는다
- 따라서 worker 수가 늘어나면 lifespan도 worker마다 각각 실행된다고 봐야 한다

### 3. 운영 파라미터를 소유한다

| 설정 | 의미 | 언제 중요하나 | 흔한 실수 |
| --- | --- | --- | --- |
| `--reload` | 코드 변경 시 재시작 | 로컬 개발 | 운영에 켠 채 배포 |
| `--workers` | 프로세스 수 | CPU 활용, 격리 | DB pool 계산 없이 감으로 증가 |
| `--proxy-headers` | reverse proxy 헤더 신뢰 | ingress/Nginx 뒤 운영 | 클라이언트 IP, scheme 오판 |
| `--timeout-keep-alive` | idle keep-alive 유지 시간 | connection churn 제어 | default 의미도 모른 채 임의 변경 |
| `--timeout-graceful-shutdown` | 종료 유예 시간 | 배포/롤링 업데이트 | shutdown 전에 요청 끊김 |
| `--limit-concurrency` | 동시 처리 상한 | downstream 보호 | 앱 내부 semaphore만 믿고 서버 상한 미설정 |

## 자주 헷갈리는 포인트

### coroutine 수와 worker 수는 다른 축이다

- worker는 프로세스 수다.
- coroutine은 worker 안 event loop 위에서 스케줄되는 작업 수다.
- worker를 4개로 늘렸다고 route가 4배 빨라지는 것은 아니다.

### `app.state`는 worker 간 공유 메모리가 아니다

- 각 worker는 독립 프로세스다.
- lifespan에서 만든 engine, cache client, in-memory dict는 worker마다 따로 생긴다.
- "한 번만 초기화된다"는 가정은 multi-worker에서 자주 깨진다.

### FastAPI route는 서버가 아니다

- timeout, keep-alive, proxy header, graceful shutdown은 route 코드가 아니라 ASGI server 설정 문제다.
- 반대로 validation, dependency graph, response model은 Uvicorn이 아니라 FastAPI 문제다.

## 개발/운영에서 최소한 구분해야 할 프로필

### 로컬 개발

- `uvicorn app.main:app --reload`
- 디버깅 편의성이 중요하다.
- 성능 숫자는 신뢰하지 않는다.

### 단순 컨테이너 운영

- reload를 끈다.
- worker 수를 DB connection budget과 같이 계산한다.
- reverse proxy 뒤면 forwarded header 설정을 명확히 둔다.

### websocket/streaming이 중요한 서비스

- ASGI와 connection lifetime을 먼저 이해해야 한다.
- Lambda보다 long-lived ASGI server가 더 자연스러운 경우가 많다.
- background task, timeout, shutdown 정책도 연결 단위로 다시 본다.

## 이 장을 읽고 바로 봐야 할 것

1. [Lifespan과 테스트](/fastapi/lifespan-and-testing)
2. [BackgroundTasks와 오프로딩](/fastapi/background-tasks-and-offloading)
3. [Performance and Ops](/fastapi/performance-and-ops)

실행 예제로는 `examples/asgi_lifecycle_lab.py`가 `scope`, `receive`, `send` 흐름을 짧게 보여준다.

## 공식 자료

- [ASGI Specification](https://asgi.readthedocs.io/en/latest/specs/main.html)
- [ASGI Introduction](https://asgi.readthedocs.io/en/latest/introduction.html)
- [Uvicorn Settings](https://www.uvicorn.org/settings/)
- [Uvicorn Server Behavior](https://www.uvicorn.org/server-behavior/)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
