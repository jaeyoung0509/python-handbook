# Uvicorn proxy and health lab: root_path, trusted host, HTTPS redirect, readiness, and profiles.
# Uvicorn proxy/헬스 실험: root_path, trusted host, HTTPS redirect, readiness, 프로필.
# Why: many production issues come from proxy and shutdown boundaries, not route code.
# 왜: 운영 이슈 상당수는 route 코드보다 proxy와 shutdown 경계에서 나온다.
# Use when: learning how app-side health checks and server-side proxy settings fit together.
# 언제 쓰나: 앱 health check와 서버 proxy 설정이 어떻게 맞물리는지 익힐 때 좋다.

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.middleware import Middleware, _MiddlewareFactory
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


@dataclass(frozen=True, slots=True)
class UvicornProfile:
    name: str
    reload: bool
    workers: int
    proxy_headers: bool
    forwarded_allow_ips: str


def suggested_flags(profile: UvicornProfile) -> list[str]:
    flags = [
        f"name={profile.name}",
        f"reload={profile.reload}",
        f"workers={profile.workers}",
    ]
    if profile.proxy_headers:
        flags.append("proxy-headers=true")
        flags.append(f"forwarded-allow-ips={profile.forwarded_allow_ips}")
    return flags


def create_app() -> FastAPI:
    trusted_host_factory = cast(_MiddlewareFactory, TrustedHostMiddleware)
    https_redirect_factory = cast(_MiddlewareFactory, HTTPSRedirectMiddleware)
    middleware = [
        Middleware(
            trusted_host_factory,
            allowed_hosts=["api.example.com", "testserver"],
        ),
        Middleware(https_redirect_factory),
    ]
    app = FastAPI(
        title="Proxy and Health Lab",
        root_path="/api/v1",
        middleware=middleware,
    )
    app.state.ready = True

    @app.get("/scope")
    def scope_info(request: Request) -> dict[str, str]:
        return {
            "scheme": request.url.scheme,
            "root_path": str(request.scope.get("root_path", "")),
            "path": str(request.scope["path"]),
        }

    @app.get("/health/live")
    def health_live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    def health_ready(request: Request) -> JSONResponse:
        is_ready = bool(getattr(request.app.state, "ready", False))
        if is_ready:
            return JSONResponse({"status": "ready"}, status_code=200)
        return JSONResponse({"status": "draining"}, status_code=503)

    @app.post("/admin/drain")
    def admin_drain(request: Request) -> dict[str, bool]:
        request.app.state.ready = False
        return {"ready": False}

    return app


def main() -> None:
    local_profile = UvicornProfile(
        name="local-dev",
        reload=True,
        workers=1,
        proxy_headers=False,
        forwarded_allow_ips="",
    )
    k8s_profile = UvicornProfile(
        name="k8s-behind-proxy",
        reload=False,
        workers=2,
        proxy_headers=True,
        forwarded_allow_ips="10.0.0.10,10.0.0.11",
    )

    app = create_app()
    with TestClient(app, base_url="http://api.example.com") as insecure_client:
        redirect_response = insecure_client.get("/health/live", follow_redirects=False)

    with TestClient(app, base_url="https://api.example.com") as secure_client:
        scope_response = secure_client.get("/scope")
        ready_before = secure_client.get("/health/ready")
        drain_response = secure_client.post("/admin/drain")
        ready_after = secure_client.get("/health/ready")
        bad_host = secure_client.get("/scope", headers={"host": "evil.example.net"})

    print("local profile:", suggested_flags(local_profile))
    print("k8s profile:", suggested_flags(k8s_profile))
    print("http redirect status:", redirect_response.status_code)
    print("scope info:", scope_response.json())
    print("ready before drain:", ready_before.status_code, ready_before.json())
    print("drain response:", drain_response.status_code, drain_response.json())
    print("ready after drain:", ready_after.status_code, ready_after.json())
    print("bad host status:", bad_host.status_code)


if __name__ == "__main__":
    main()
