# Proxy, Health, Shutdown

<p class="lead">로컬에서 `uvicorn main:app --reload`로 잘 돌던 서비스가 실제 배포에서 어긋나는 지점은 대부분 앱 코드 자체보다 운영 경계에서 나온다. reverse proxy, `root_path`, forwarded headers, readiness, graceful shutdown을 따로 이해하지 않으면 "문서는 맞는데 운영이 이상한" 상태가 생긴다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: proxy 뒤 배포에서는 `root_path`, trusted forwarded header, host/scheme 인식이 중요하고, Kubernetes 같은 환경에서는 liveness/readiness/startup probe를 역할별로 나눠야 한다. graceful shutdown은 "프로세스를 죽이기 전 준비 안 됨 상태로 빼고, 새 요청을 막고, 열린 작업을 정리한 뒤 종료"하는 순서로 봐야 한다.</p>
</div>

## 전체 그림

<MermaidDiagram
  caption="실서비스에서는 앱이 직접 인터넷과 만나는 경우보다 proxy와 오케스트레이터 뒤에 있는 경우가 더 흔하다."
  chart="flowchart LR; A[&quot;Client&quot;] --> B[&quot;Reverse proxy or ingress&quot;]; B --> C[&quot;Uvicorn workers&quot;]; C --> D[&quot;FastAPI app&quot;]; D --> E[&quot;Readiness and liveness endpoints&quot;]; C --> F[&quot;Graceful shutdown and drain&quot;];"
/>

## 1) reverse proxy 뒤에서는 `root_path`를 이해해야 한다

proxy가 `/api/v1` 같은 path prefix를 바깥에서 붙이고, 내부 앱은 여전히 `/users` 같은 경로만 안다고 하자. 이때 ASGI의 `root_path`가 연결 고리가 된다.

```py
from fastapi import FastAPI, Request

app = FastAPI(root_path="/api/v1")


@app.get("/users")
def read_users(request: Request) -> dict[str, str]:
    return {
        "path": request.scope["path"],
        "root_path": request.scope.get("root_path", ""),
    }
```

중요한 점:

- `root_path`는 "공식 외부 경로 prefix"를 앱에 알려준다.
- FastAPI 문서 UI와 OpenAPI server URL도 여기에 영향을 받는다.
- Uvicorn이 직접 `/api/v1/users`를 이해하는 것이 아니라, proxy가 prefix를 처리하고 앱에는 `root_path` 정보를 넘기는 구조다.

## 2) forwarded header는 "신뢰 가능한 proxy만" 믿어야 한다

Uvicorn 공식 문서 기준으로 `--proxy-headers`와 `--forwarded-allow-ips`를 통해 `X-Forwarded-Proto`, `X-Forwarded-For` 같은 헤더를 해석할 수 있다. 하지만 이 헤더는 누구나 보낼 수 있으므로, 실제로 신뢰할 수 있는 proxy IP만 믿어야 한다.

| 항목 | 왜 필요한가 | 흔한 실수 |
| --- | --- | --- |
| `--proxy-headers` | scheme, client address 해석 | proxy 뒤인데 비활성화해 URL/scheme 오판 |
| `--forwarded-allow-ips` | 어떤 hop를 믿을지 제한 | `*`를 무심코 사용 |
| `TrustedHostMiddleware` | Host 헤더 제한 | 아무 host나 허용 |
| `HTTPSRedirectMiddleware` | HTTP를 HTTPS로 유도 | ingress가 이미 처리하는데 중복 구성 |

## 3) health endpoint는 하나가 아니라 역할이 다르다

Kubernetes 공식 문서 기준으로 probe는 역할이 다르다.

| probe | 질문 | 실패 시 의미 |
| --- | --- | --- |
| liveness | 프로세스가 죽었거나 deadlock인가 | 재시작 후보 |
| readiness | 지금 트래픽을 받아도 되는가 | service endpoint에서 제외 |
| startup | 초기화가 아직 끝나지 않았는가 | liveness/readiness 시작 전 대기 |

### 실무 기준

- liveness는 너무 무겁게 만들지 않는다.
- readiness는 DB, cache, warmup, drain 상태를 반영할 수 있다.
- startup probe가 필요한 느린 앱이라면 liveness가 너무 빨리 restart하지 않게 막는다.

## 4) graceful shutdown은 "drain -> 정리 -> 종료" 순서로 본다

좋은 종료 순서:

1. readiness를 실패 상태로 바꿔 새 트래픽 유입을 줄인다.
2. 열린 요청과 연결이 끝날 시간을 잠깐 준다.
3. lifespan shutdown에서 engine, client, consumer를 닫는다.
4. 유예 시간 안에 못 끝난 작업은 timeout 정책에 따라 끊는다.

자주 하는 실수:

- SIGTERM이 오자마자 프로세스를 바로 죽인다.
- readiness와 shutdown을 연결하지 않는다.
- WebSocket이나 streaming connection drain 시간을 고려하지 않는다.
- 긴 background 작업을 API 프로세스 안에 남겨 둔다.

## 5) middleware로 운영 가드레일을 둘 수 있다

```py
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.example.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

이런 middleware는 앱 레벨에서 host/scheme 가드레일을 두는 용도다. 다만 ingress나 load balancer가 이미 같은 일을 하고 있다면 중복 리다이렉트나 오동작이 없는지 확인해야 한다.

## 6) 운영 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>`root_path` 확인</h3>
    <p>proxy가 path prefix를 다룬다면 docs URL과 OpenAPI server URL이 올바른지 함께 본다.</p>
  </div>
  <div class="check-card">
    <h3>trusted proxy 제한</h3>
    <p>forwarded header는 실제로 신뢰할 hop만 허용한다. 그렇지 않으면 client IP와 scheme spoofing 위험이 생긴다.</p>
  </div>
  <div class="check-card">
    <h3>probe 역할 분리</h3>
    <p>liveness는 "살아 있는가", readiness는 "받아도 되는가", startup은 "준비 중인가"를 분리해서 본다.</p>
  </div>
  <div class="check-card">
    <h3>drain 가능한 종료</h3>
    <p>shutdown 전에 readiness를 내려 트래픽을 빼고, 긴 연결과 자원 정리를 위한 시간을 확보한다.</p>
  </div>
</div>

## 같이 읽으면 좋은 페이지

1. [ASGI와 Uvicorn](/fastapi/asgi-and-uvicorn)
2. [WebSocket, Streaming, Middleware](/fastapi/websockets-streaming-and-middleware)
3. [Lambda vs Kubernetes](/playbooks/lambda-vs-kubernetes)

실행 예제로는 `examples/uvicorn_proxy_and_health_lab.py`를 같이 보면 `root_path`, trusted host, HTTPS redirect, readiness 전환 감각을 빠르게 볼 수 있다.

## 공식 자료

- [FastAPI Behind a Proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
- [Uvicorn Settings](https://www.uvicorn.org/settings/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
- [Kubernetes Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
