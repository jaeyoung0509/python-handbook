from __future__ import annotations

# What this lab adds / 이 예제가 추가하는 것:
# - Show dependency-based authentication and authorization separation.
# - dependency 기반 authentication / authorization 분리를 보여준다.
# - Compare bearer-token auth with cookie-session auth in one runnable app.
# - bearer token auth와 cookie session auth를 한 앱 안에서 비교한다.
# - Demonstrate why cookie auth needs CSRF protection.
# - cookie auth에 왜 CSRF 방어가 필요한지 보여준다.
#
# Why it was added / 왜 추가되었나:
# - Security discussions stay abstract unless the auth boundary is executable.
# - auth 경계는 실행 가능한 코드가 있어야 추상론으로 끝나지 않는다.
# - Many teams mix token parsing, policy checks, and business logic in routes.
# - 많은 팀이 route에서 token parsing, policy, business logic를 한데 섞는다.
#
# When to use this / 언제 보면 좋은가:
# - When choosing between session cookies and bearer tokens.
# - session cookie와 bearer token 중 무엇을 쓸지 고민할 때.
# - When designing `CurrentUser` dependencies and admin-only policies.
# - `CurrentUser` dependency와 admin-only policy를 설계할 때.
import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

SECRET = b"python-handbook-demo-secret"


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: str
    role: str


USER_DIRECTORY = {
    "neo": CurrentUser(user_id="neo", role="member"),
    "trinity": CurrentUser(user_id="trinity", role="member"),
    "architect": CurrentUser(user_id="architect", role="admin"),
}

BEARER_TOKENS = {
    "member-token": USER_DIRECTORY["neo"],
    "admin-token": USER_DIRECTORY["architect"],
}

bearer_scheme = HTTPBearer(auto_error=False)


def sign_payload(payload: dict[str, str]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("utf-8")
    signature = hmac.new(SECRET, encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def unsign_payload(token: str) -> dict[str, str] | None:
    try:
        encoded, provided_signature = token.rsplit(".", maxsplit=1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        SECRET,
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, provided_signature):
        return None

    decoded = base64.urlsafe_b64decode(encoded.encode("utf-8"))
    return cast(dict[str, str], json.loads(decoded.decode("utf-8")))


def get_bearer_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    user = BEARER_TOKENS.get(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid bearer token")
    return user


def require_admin(
    user: Annotated[CurrentUser, Depends(get_bearer_user)],
) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user


def get_session_user(request: Request) -> CurrentUser:
    signed_cookie = request.cookies.get("session")
    if signed_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing session cookie")

    payload = unsign_payload(signed_cookie)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session cookie")

    user_id = payload.get("user_id")
    role = payload.get("role")
    if user_id is None or role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="broken session payload")

    return CurrentUser(user_id=user_id, role=role)


def require_csrf(request: Request) -> None:
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("x-csrf-token")
    if cookie_token is None or header_token is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="missing csrf token")
    if not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="csrf token mismatch")


def create_app() -> FastAPI:
    app = FastAPI(title="security-auth-lab")

    @app.post("/session-login/{user_id}")
    def session_login(user_id: str, response: Response) -> dict[str, str]:
        user = USER_DIRECTORY.get(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown demo user")
        session_payload = {"user_id": user.user_id, "role": user.role}
        csrf_token = secrets.token_hex(8)

        response.set_cookie("session", sign_payload(session_payload), httponly=True, samesite="lax")
        response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="lax")
        return {"status": "ok", "csrf_token": csrf_token}

    @app.get("/cookie/me")
    def cookie_me(
        user: Annotated[CurrentUser, Depends(get_session_user)],
    ) -> dict[str, str]:
        return {"user_id": user.user_id, "role": user.role}

    @app.post("/cookie/change-email")
    def cookie_change_email(
        _: Annotated[None, Depends(require_csrf)],
        user: Annotated[CurrentUser, Depends(get_session_user)],
    ) -> dict[str, str]:
        return {"status": "queued", "by": user.user_id}

    @app.get("/bearer/admin-report")
    def bearer_admin_report(
        admin: Annotated[CurrentUser, Depends(require_admin)],
    ) -> dict[str, str]:
        return {"status": "granted", "admin": admin.user_id}

    return app


def main() -> None:
    app = create_app()
    with TestClient(app) as client:
        print("== bearer token flow ==")
        denied = client.get(
            "/bearer/admin-report",
            headers={"Authorization": "Bearer member-token"},
        )
        allowed = client.get(
            "/bearer/admin-report",
            headers={"Authorization": "Bearer admin-token"},
        )
        print(f"member token status: {denied.status_code}")
        print(f"admin token body: {allowed.json()}")

        print("\n== cookie session with csrf ==")
        login_response = client.post("/session-login/neo")
        csrf_token = login_response.json()["csrf_token"]
        me_response = client.get("/cookie/me")
        missing_csrf = client.post("/cookie/change-email")
        valid_csrf = client.post(
            "/cookie/change-email",
            headers={"x-csrf-token": csrf_token},
        )

        print(f"session profile: {me_response.json()}")
        print(f"missing csrf status: {missing_csrf.status_code}")
        print(f"valid csrf body: {valid_csrf.json()}")


if __name__ == "__main__":
    main()
