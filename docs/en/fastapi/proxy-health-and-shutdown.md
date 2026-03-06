# Proxy, Health, and Shutdown

<p class="lead">A service that works locally with `uvicorn main:app --reload` can still behave differently in production because the operational boundary is different. Reverse proxies, `root_path`, forwarded headers, readiness, and graceful shutdown are where many "the code looks right, but production is odd" problems actually come from.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: behind a proxy, `root_path`, trusted forwarded headers, and correct host or scheme handling matter. In environments such as Kubernetes, liveness, readiness, and startup probes should have distinct roles. Graceful shutdown is best modeled as "become unready, stop accepting new traffic, drain and clean up, then exit".</p>
</div>

## The full picture

<MermaidDiagram
  caption="Production services more often sit behind proxies and orchestrators than they sit directly on the public edge."
  chart="flowchart LR; A[&quot;Client&quot;] --> B[&quot;Reverse proxy or ingress&quot;]; B --> C[&quot;Uvicorn workers&quot;]; C --> D[&quot;FastAPI app&quot;]; D --> E[&quot;Readiness and liveness endpoints&quot;]; C --> F[&quot;Graceful shutdown and drain&quot;];"
/>

## 1) Understand `root_path` behind a reverse proxy

Suppose the proxy exposes the app under `/api/v1`, while the app code itself still declares routes such as `/users`. In ASGI, `root_path` is the mechanism that communicates that external mount prefix.

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

Important points:

- `root_path` tells the app about the external path prefix
- FastAPI docs UI and generated OpenAPI server URLs are affected by it
- Uvicorn does not magically understand the external prefix by itself; the proxy handles the public path while the app receives the ASGI `root_path`

## 2) Only trust forwarded headers from proxies you actually trust

According to the Uvicorn docs, `--proxy-headers` and `--forwarded-allow-ips` control how headers such as `X-Forwarded-Proto` and `X-Forwarded-For` are interpreted. Those headers can be forged, so you should only trust them from proxy hops you control.

| Setting or tool | Why it matters | Common mistake |
| --- | --- | --- |
| `--proxy-headers` | interpret scheme and client address | leaving it off behind a proxy and misreading URL or scheme |
| `--forwarded-allow-ips` | restrict which hops are trusted | using `*` casually |
| `TrustedHostMiddleware` | constrain accepted Host headers | allowing arbitrary hosts |
| `HTTPSRedirectMiddleware` | redirect plain HTTP to HTTPS | duplicating behavior already handled at ingress |

## 3) Health endpoints are not all the same

The Kubernetes docs distinguish probe roles clearly.

| Probe | Question | Meaning of failure |
| --- | --- | --- |
| liveness | is the process dead or stuck | candidate for restart |
| readiness | should traffic reach this instance right now | remove from service endpoints |
| startup | has initialization finished yet | delay liveness and readiness checks |

### Practical guidance

- keep liveness checks lightweight
- let readiness reflect DB, cache, warmup, or drain state
- use startup probes for slow-starting services so liveness does not restart them too early

## 4) Model graceful shutdown as "drain, clean up, exit"

A good shutdown sequence:

1. mark readiness as failed so new traffic stops arriving
2. allow in-flight requests and connections some time to finish
3. close engines, clients, and consumers in lifespan shutdown
4. enforce timeout policy if work does not finish within the grace period

Common mistakes:

- killing the process immediately on SIGTERM
- never connecting readiness state to shutdown behavior
- forgetting long-lived websocket or streaming connections
- leaving long-running background work inside the API process

## 5) Middleware can add operational guardrails

```py
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.example.com", "*.example.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

These are app-level guardrails for host and scheme handling. But if ingress or the load balancer already owns those concerns, double redirects or contradictory behavior are easy to introduce, so align the layers deliberately.

## 6) Operational checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Verify `root_path`</h3>
    <p>If the proxy adds a path prefix, make sure docs URLs and generated server URLs still match the public path.</p>
  </div>
  <div class="check-card">
    <h3>Constrain trusted proxies</h3>
    <p>Only trust forwarded headers from actual proxy hops you control, otherwise client or scheme spoofing becomes possible.</p>
  </div>
  <div class="check-card">
    <h3>Separate probe roles</h3>
    <p>Liveness answers "am I alive", readiness answers "should I receive traffic", and startup answers "am I ready to begin checks".</p>
  </div>
  <div class="check-card">
    <h3>Support drain before exit</h3>
    <p>Drop readiness before shutdown so new traffic stops, then give long-lived work time to close cleanly.</p>
  </div>
</div>

## Companion chapters

1. [ASGI and Uvicorn](/en/fastapi/asgi-and-uvicorn)
2. [WebSockets, Streaming, and Middleware](/en/fastapi/websockets-streaming-and-middleware)
3. [Lambda vs Kubernetes](/en/playbooks/lambda-vs-kubernetes)

For runnable intuition, pair this chapter with `examples/uvicorn_proxy_and_health_lab.py`.

## Official References

- [FastAPI Behind a Proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
- [Uvicorn Settings](https://www.uvicorn.org/settings/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
- [Kubernetes Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
