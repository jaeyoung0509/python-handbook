# 웹 게이트웨이 진화: CGI, WSGI, ASGI

<p class="lead">Python 웹 프레임워크를 제대로 이해하려면 FastAPI나 Django부터 보는 것보다 먼저 "서버가 애플리케이션을 어떤 인터페이스로 호출하는가"를 봐야 한다. CGI, WSGI, ASGI는 단순한 약어가 아니라, Python 웹이 어떤 병목과 요구를 만나면서 인터페이스를 바꿔왔는지를 보여주는 역사다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: CGI는 요청마다 프로세스를 띄우는 가장 단순한 모델이었고, WSGI는 장수 프로세스 기반의 동기 HTTP 표준으로 Python 웹 생태계를 통합했다. ASGI는 `asyncio` 시대의 요구에 맞춰 `scope`, `receive`, `send`를 중심으로 HTTP, WebSocket, lifespan, streaming까지 다루는 connection/event 인터페이스로 확장했다.</p>
</div>

## 왜 "게이트웨이 인터페이스"가 필요한가

- 웹 서버는 소켓, 프로세스, 연결, timeout, proxy 같은 바깥 문제를 다룬다.
- 애플리케이션은 라우팅, 비즈니스 로직, 템플릿, validation 같은 안쪽 문제를 다룬다.
- 둘 사이 계약이 표준화되어야 같은 앱을 다른 서버에서 돌릴 수 있고, 같은 서버 위에 다른 프레임워크도 올릴 수 있다.

<MermaidDiagram
  caption="Python 웹 인터페이스는 서버와 애플리케이션 사이의 경계를 시대별 요구에 맞게 다시 정의해 왔다."
  chart="flowchart LR; A[&quot;CGI&quot;] --> B[&quot;WSGI&quot;]; B --> C[&quot;ASGI&quot;]; A --> D[&quot;Process per request&quot;]; B --> E[&quot;Sync request and response&quot;]; C --> F[&quot;Async connection and events&quot;];"
/>

## 1) CGI: 가장 단순했지만 요청당 비용이 컸다

CGI(Common Gateway Interface)는 웹 서버가 요청을 받을 때마다 외부 프로그램을 실행하고, 환경 변수와 표준 입출력으로 데이터를 주고받는 모델이다.

### 왜 당시에는 괜찮았나

- 구현이 단순했다.
- 언어와 서버가 강하게 묶이지 않았다.
- "HTTP 요청 하나 -> 프로그램 실행 하나"라는 모델이 직관적이었다.

### 왜 한계가 빨리 드러났나

- 요청마다 프로세스를 새로 띄우는 비용이 컸다.
- DB connection, 캐시, 앱 초기화 상태를 재사용하기 어려웠다.
- 긴 연결, streaming, websocket 같은 현대적 요구를 다루기 불편했다.

CGI는 "웹 서버가 외부 애플리케이션을 실행한다"는 큰 아이디어를 열었지만, Python 웹 프레임워크가 커지기에는 프로세스 모델이 너무 비쌌다.

## 2) WSGI: Python 웹 생태계를 묶어낸 공통 계약

WSGI(Web Server Gateway Interface)는 PEP 3333에서 정의한 Python 웹 애플리케이션 인터페이스다. 핵심은 "웹 서버와 프레임워크가 같은 함수 시그니처로 만난다"는 점이다.

```py
def application(environ, start_response):
    ...
```

### WSGI가 해결한 문제

- 장수 프로세스나 worker 안에서 앱을 계속 재사용할 수 있었다.
- 서버와 프레임워크 조합이 쉬워졌다.
- middleware를 함수 조합처럼 쌓는 패턴이 퍼졌다.
- Python 웹 생태계가 "서버별 전용 API"에서 벗어날 수 있었다.

### 왜 WSGI는 그 시대에 잘 맞았나

- 대부분의 웹 애플리케이션이 동기 request/response HTTP 중심이었다.
- thread/process worker 모델이 자연스러웠다.
- Django, Flask 같은 프레임워크의 핵심 문제는 "동시성"보다 "이식 가능한 표준 계약"이었다.

### WSGI가 버거워진 지점

- WebSocket처럼 요청/응답 한 번으로 끝나지 않는 연결
- SSE, streaming response, long polling
- async DB client, async HTTP client처럼 awaitable I/O
- startup/shutdown 같은 app lifespan 표준화 부재

즉, WSGI는 "동기 HTTP 한 번 처리"에는 훌륭했지만, 연결이 오래 살고 이벤트가 여러 번 오가는 모델에는 맞지 않았다.

## 3) ASGI: 요청이 아니라 연결과 이벤트를 표준화

ASGI(Asynchronous Server Gateway Interface)는 WSGI의 교체재라기보다, 더 넓은 문제를 풀기 위한 확장된 인터페이스다. 기본 callable은 다음처럼 생긴다.

```py
async def app(scope, receive, send):
    ...
```

### ASGI가 새로 가져온 것

- `scope`: 연결의 정적 정보
- `receive`: 서버에서 애플리케이션으로 들어오는 이벤트
- `send`: 애플리케이션에서 서버로 나가는 이벤트
- protocol type: `http`, `websocket`, `lifespan`

### 왜 ASGI가 필요해졌나

- `asyncio`가 Python 표준 동시성 축으로 자리 잡았다.
- HTTP뿐 아니라 WebSocket과 lifespan을 같은 인터페이스에서 다뤄야 했다.
- "한 요청을 처리하는 함수"보다 "연결 위에서 이벤트를 주고받는 앱"이 더 자연스러운 시대가 되었다.

ASGI는 WSGI보다 한 단계 더 낮은 곳에서 "소켓 바이트"를 다루는 것은 아니지만, 최소한 "요청 한 번"보다 더 넓은 단위인 "연결과 이벤트 흐름"을 표준화한다.

## CGI, WSGI, ASGI를 한 줄씩 비교하면

| 인터페이스 | 주된 단위 | 대표 형태 | 잘 맞는 시대 | 한계 |
| --- | --- | --- | --- | --- |
| CGI | 프로세스 | 환경 변수 + stdin/stdout | 초기 웹, 단순 동적 페이지 | 요청당 프로세스 비용 |
| WSGI | 동기 요청/응답 | `application(environ, start_response)` | 동기 HTTP 웹 앱 | websocket, async, lifespan |
| ASGI | 연결/이벤트 | `async def app(scope, receive, send)` | async HTTP, websocket, streaming | 더 많은 런타임 이해가 필요 |

## 실무 감각으로 번역하면

- CGI: "실행" 인터페이스
- WSGI: "동기 HTTP 요청" 인터페이스
- ASGI: "연결과 이벤트" 인터페이스

FastAPI를 이해할 때 중요한 건 "FastAPI가 빠르다"가 아니라 "FastAPI는 ASGI app이고, Uvicorn 같은 ASGI server가 그 앱을 실행한다"는 사실이다.

## 이 저장소에서 이어서 읽을 곳

1. [ASGI와 Uvicorn](/fastapi/asgi-and-uvicorn)
2. [Lifespan과 테스트](/fastapi/lifespan-and-testing)
3. [BackgroundTasks와 오프로딩](/fastapi/background-tasks-and-offloading)

실행 예제로는 `examples/asgi_lifecycle_lab.py`를 같이 보면 `scope`, `receive`, `send` 감각이 빨리 잡힌다.

## 공식 자료

- [PEP 3333 - WSGI for Python 3](https://peps.python.org/pep-3333/)
- [ASGI Specification](https://asgi.readthedocs.io/en/latest/specs/main.html)
- [ASGI Introduction](https://asgi.readthedocs.io/en/latest/introduction.html)
- [PEP 3156 - asyncio](https://peps.python.org/pep-3156/)
