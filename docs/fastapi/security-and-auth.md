# Security and Auth

<p class="lead">FastAPI에서 security를 잘 설계한다는 것은 dependency 몇 개를 붙이는 기술이 아니다. 인증(authentication)은 "누구인가"를 증명하고, 인가(authorization)는 "무엇을 해도 되는가"를 결정한다. 이 둘을 route, service, persistence와 어디서 나눌지 흐리면 토큰 파싱, 정책 판단, DB 조회, HTTP 에러가 한 함수에 엉킨다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: FastAPI dependency는 credential parsing과 current principal 복원까지 맡고, 권한 정책은 명시적인 dependency 또는 service policy로 둔다. cookie session, bearer token, API key 중 무엇을 고를지는 "클라이언트 종류", "revocation 필요성", "CSRF 표면", "운영 단순성"으로 결정하는 편이 맞다.</p>
</div>

<MermaidDiagram
  caption="좋은 auth 흐름은 credential parsing, principal 복원, policy check, use case 실행이 분리되어 있다."
  chart="flowchart LR; A[&quot;Request&quot;] --> B[&quot;credential extraction&quot;]; B --> C[&quot;authenticate principal&quot;]; C --> D[&quot;authorization policy&quot;]; D --> E[&quot;service or use case&quot;]; E --> F[&quot;response&quot;];"
/>

## 1) 먼저 경계를 나눈다: authn과 authz는 다르다

### authentication

- credential를 읽는다.
- token, cookie, API key를 검증한다.
- `CurrentUser` 또는 principal object를 만든다.

### authorization

- 이 principal이 현재 action을 수행해도 되는지 판단한다.
- role, scope, ownership, tenant boundary를 본다.
- 보통 route 바로 바깥 또는 service policy에서 체크한다.

좋지 않은 패턴은 "JWT decode + DB 조회 + role 분기 + 비즈니스 규칙"을 endpoint 함수 하나에 몰아넣는 것이다.

## 2) 어떤 credential 방식을 고를까

| 방식 | 잘 맞는 경우 | 장점 | 주의점 |
| --- | --- | --- | --- |
| cookie session | 같은 도메인 브라우저 앱, server-side revoke가 중요한 경우 | 브라우저와 잘 맞고 강제 로그아웃이 쉬움 | CSRF 방어 필요, cookie 속성 관리 필요 |
| bearer token / JWT | 모바일 앱, 외부 API client, gateway 연동 | header 기반이라 transport가 단순 | revocation, rotation, audience, expiry 설계를 빼먹기 쉬움 |
| API key | server-to-server, 내부 batch, 단순 automation | 구현이 단순 | 권한 범위와 rotation이 약하면 위험 |

### session cookie가 좋은 경우

- 브라우저 기반 first-party 앱
- session revoke가 자주 필요
- refresh / logout / device 정책을 서버가 더 강하게 통제해야 함

### bearer token이 좋은 경우

- 모바일 앱, CLI, third-party client
- API gateway 또는 identity provider와 연동
- cross-domain 브라우저보다는 non-browser client 비중이 큼

### JWT를 쓴다고 자동으로 쉬워지지 않는다

JWT는 "stateless"라는 장점이 있지만, 실제 운영에서는 아래를 여전히 정해야 한다.

- key rotation
- issuer / audience 검증
- expiry 정책
- refresh 전략
- revoke 또는 force logout 필요 시 어떻게 할지

## 3) FastAPI dependency는 어디까지 책임져야 하나

좋은 baseline은 아래 네 층이다.

1. transport extraction: header/cookie/query에서 credential 읽기
2. authentication: principal 복원
3. authorization: role/scope/ownership 정책 확인
4. use case: 실제 business action 실행

```py
from typing import Annotated

from fastapi import Depends, HTTPException, status


class CurrentUser(BaseModel):
    user_id: str
    role: str


def get_current_user(token: Annotated[str, Depends(read_bearer_token)]) -> CurrentUser:
    payload = decode_and_validate_token(token)
    return CurrentUser(user_id=payload.sub, role=payload.role)


def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user
```

<p class="code-caption">중요한 점은 endpoint가 token parsing 상세를 몰라도 된다는 것이다. endpoint는 이미 복원된 principal 또는 policy 통과 결과를 받는 편이 훨씬 읽기 쉽다.</p>

## 4) cookie session과 JWT를 비교할 때 꼭 봐야 할 것

### cookie session

- server-side session store 또는 signed cookie를 쓸 수 있다.
- 브라우저가 자동으로 cookie를 보내므로 UX는 편하다.
- 그래서 CSRF 방어를 별도로 해야 한다.

권장 체크:

- `HttpOnly`
- `Secure`
- `SameSite`
- session rotation on login
- logout / revoke path

### bearer token / JWT

- 보통 `Authorization: Bearer ...` header로 전달한다.
- 브라우저가 자동 전송하지 않으므로 CSRF 표면은 다르다.
- 대신 XSS, token leakage, refresh token 보관 위치가 중요해진다.

권장 체크:

- short-lived access token
- refresh token 분리
- key rotation
- audience / issuer 검증
- client별 storage 전략

## 5) CORS와 CSRF는 다른 문제다

이 둘을 자주 혼동한다.

| 항목 | 질문 | 주로 중요한 경우 |
| --- | --- | --- |
| CORS | 브라우저가 이 출처에 cross-origin 요청을 허용하는가 | 브라우저 프론트엔드 |
| CSRF | 사용자의 브라우저가 원치 않는 credential 포함 요청을 보내게 만들 수 있는가 | cookie auth |

### 기억해야 할 규칙

- CORS는 보안 경계 전체를 대신하지 않는다.
- cookie 기반 auth는 CORS를 맞춰도 CSRF 방어가 별도로 필요하다.
- bearer token을 `Authorization` header로 보내는 구조는 cookie auth보다 CSRF 표면이 작지만, XSS 위험은 여전히 중요하다.

## 6) password와 secret을 다루는 기본 원칙

- 비밀번호는 reversible encryption이 아니라 password hashing으로 저장한다.
- modern password hashing(`Argon2id`, `scrypt`, `bcrypt`) 중 팀 기준을 명확히 잡는다.
- JWT signing key, session secret, API key는 `settings.py` + secret source로 관리한다.
- secret rotation 경로를 미리 만들어 둔다.

FastAPI 문서 자체는 security primitives를 제공하지만, password hashing 알고리즘 선택과 운영 정책은 애플리케이션 책임이다.

## 7) authorization은 role만으로 끝나지 않는다

role check는 시작일 뿐이다.

실무에서는 보통 아래까지 필요하다.

- ownership: 이 리소스가 이 사용자 것인가
- tenant boundary: 같은 role이어도 tenant가 다르면 접근 금지
- action scope: `read:orders`, `write:orders`
- environment policy: 운영자 API는 내부 네트워크 또는 별도 MFA 요구

이 판단이 커지면 dependency 한 줄로 끝내기보다 service policy object로 분리하는 편이 낫다.

## 8) WebSocket auth는 HTTP auth와 닮았지만 같지 않다

WebSocket은 connect 시 한 번 인증하고 이후 메시지별 인가를 추가로 둘 수 있다.

- connect 시 token 또는 cookie 확인
- room join, command 실행 시 message-level authorization
- disconnect cleanup
- invalid token close code 정책

즉, "연결을 열 수 있는가"와 "이 메시지를 보낼 수 있는가"를 분리해서 생각해야 한다.

## 9) 에러와 로깅도 security 설계의 일부다

- 잘못된 credential: `401 Unauthorized`
- 인증은 됐지만 권한 없음: `403 Forbidden`
- credential가 없다고 사용자 존재 여부를 과하게 노출하지 않는다.
- auth failure는 structured logging으로 남기되 raw secret은 절대 로그에 남기지 않는다.

rate limiting, audit logging, suspicious activity detection도 auth 이후에 붙는 운영 축이다.

## 10) 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>authn과 authz를 분리했는가</h3>
    <p>credential parsing과 policy 판단이 한 함수에 섞이지 않아야 한다.</p>
  </div>
  <div class="check-card">
    <h3>cookie와 token의 threat model을 구분했는가</h3>
    <p>browser/cross-origin/CSRF/XSS 표면이 다르다.</p>
  </div>
  <div class="check-card">
    <h3>revoke/rotation 이야기가 있는가</h3>
    <p>JWT를 써도 force logout, key rotation이 필요할 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>WebSocket auth까지 생각했는가</h3>
    <p>HTTP route만 보호하고 realtime path를 비워두지 않는다.</p>
  </div>
</div>

## 이 저장소에서 같이 볼 문서

1. [Request/Response Modeling](/fastapi/request-response-modeling)
2. [BackgroundTasks와 오프로딩](/fastapi/background-tasks-and-offloading)
3. [WebSocket 실전 패턴](/fastapi/websocket-practical-patterns)
4. [Settings와 Pydantic Settings](/playbooks/settings-and-pydantic-settings)

실행 예제는 `examples/fastapi_security_auth_lab.py`를 참고하면 된다.

## 공식 자료

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette Authentication](https://www.starlette.io/authentication/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [RFC 7519 - JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
