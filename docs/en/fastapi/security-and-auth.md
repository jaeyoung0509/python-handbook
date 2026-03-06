# Security and Auth

<p class="lead">In FastAPI, good security design is not about sprinkling a few dependencies on routes. Authentication proves who the caller is. Authorization decides what that caller may do. If those responsibilities blur together with route logic, token parsing, policy checks, database access, and HTTP errors quickly collapse into one endpoint function.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: let FastAPI dependencies handle credential extraction and principal restoration, then keep authorization as an explicit dependency or service-layer policy. Choose between session cookies, bearer tokens, and API keys based on client type, revocation needs, CSRF surface, and operational simplicity.</p>
</div>

<MermaidDiagram
  caption="A clean auth flow keeps credential extraction, principal restoration, policy checks, and use-case execution separate."
  chart="flowchart LR; A[&quot;Request&quot;] --> B[&quot;credential extraction&quot;]; B --> C[&quot;authenticate principal&quot;]; C --> D[&quot;authorization policy&quot;]; D --> E[&quot;service or use case&quot;]; E --> F[&quot;response&quot;];"
/>

## 1) Split the boundary first: authn and authz are not the same

### authentication

- read the credential
- validate the token, cookie, or API key
- restore a `CurrentUser` or principal object

### authorization

- decide whether that principal may perform the current action
- check role, scope, ownership, or tenant boundary
- keep the rule near the route boundary or in a dedicated service policy

A bad pattern is to pack JWT decode, DB lookups, role branching, and domain rules into the same endpoint function.

## 2) Which credential style should you use?

| Style | Good fit | Strength | Main caution |
| --- | --- | --- | --- |
| session cookie | same-domain browser apps, strong server-side revoke needs | browser-friendly and easy forced logout | needs CSRF protection and careful cookie attributes |
| bearer token / JWT | mobile apps, external API clients, gateway integration | simple transport over headers | revocation, rotation, audience, and expiry are easy to under-design |
| API key | server-to-server calls, internal automation, simple batch jobs | simple to implement | weak if scope and rotation are not disciplined |

### When session cookies fit well

- first-party browser applications
- strong logout or session revocation requirements
- device or session management owned by the server

### When bearer tokens fit well

- mobile apps, CLIs, third-party clients
- gateway or identity-provider integration
- non-browser client traffic dominates

### JWT does not remove operational work

Even with JWTs you still need answers for:

- key rotation
- issuer and audience validation
- expiry policy
- refresh strategy
- revocation or forced logout requirements

JWT especially gets misread here. "Stateless" does not mean "instant revocation is free".

- if you need forced logout, account lock, or rapid response to credential leakage, you usually need server-side state again through deny lists, token versions, session records, or very short access-token TTLs
- for first-party browser apps, session cookies or a BFF pattern can easily be the simpler operational choice

## 3) How far should FastAPI dependencies go?

A solid baseline is to separate four layers:

1. transport extraction: read credential from header, cookie, or query
2. authentication: restore the principal
3. authorization: check role, scope, or ownership
4. use case: execute the business action

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

<p class="code-caption">The endpoint should not need to know token-decoding details. It is much easier to read once the route receives a restored principal or an already-passed policy result.</p>

## 4) The real comparison: cookies vs JWT

### session cookie

- can use either a server-side session store or a signed cookie
- fits browser UX well because the browser sends cookies automatically
- therefore requires separate CSRF protection

Recommended checks:

- `HttpOnly`
- `Secure`
- `SameSite`
- session rotation on login
- clear logout and revoke behavior

### bearer token / JWT

- usually travels in the `Authorization: Bearer ...` header
- not sent automatically by the browser in the same way as cookies
- reduces CSRF exposure compared with cookie auth, but XSS and token storage still matter

Recommended checks:

- short-lived access tokens
- refresh token separation
- key rotation
- issuer and audience validation
- deliberate client-side storage rules

Browser storage deserves explicit caution.

- `localStorage` and `sessionStorage` are convenient, but an XSS issue can turn them into a token-exfiltration path
- if a browser app must handle access tokens directly, memory-only storage plus short TTLs and a clear refresh path is usually safer than treating storage as an afterthought
- for first-party web apps, `HttpOnly` cookies or a BFF design are often the more conservative default

## 5) CORS and CSRF are not the same problem

Teams confuse these all the time.

| Topic | Core question | Mostly matters for |
| --- | --- | --- |
| CORS | may the browser make this cross-origin request? | browser frontends |
| CSRF | can a browser be tricked into sending authenticated requests? | cookie auth |

### Rules worth memorizing

- CORS is not your full security boundary.
- Cookie-based auth still needs CSRF protection even when CORS is configured correctly.
- Bearer tokens sent in headers reduce CSRF exposure, but XSS is still critical.

## 6) Basic rules for passwords and secrets

- store passwords with password hashing, not reversible encryption
- choose a modern password hashing algorithm such as `Argon2id`, `scrypt`, or `bcrypt`
- manage JWT signing keys, session secrets, and API keys through `settings.py` plus secret sources
- design a rotation path early

FastAPI provides security primitives, but hashing policy and secret operations still belong to the application.

It also helps not to blur OAuth2 and OIDC.

- OAuth2 is mainly a delegated-authorization framework
- OIDC adds an identity layer on top so you can reason about who signed in
- for social login, enterprise SSO, or external identity-provider integration, a proven OIDC provider is almost always cheaper than building the stack yourself
- once you start implementing password reset, MFA, device management, and federation yourself, you are no longer "adding auth", you are building an account platform

## 7) Authorization is rarely just a role check

Role checks are only the start.

Real systems often need:

- ownership: does this resource belong to this user?
- tenant boundary: same role, different tenant, still forbidden
- action scope: `read:orders`, `write:orders`
- environment policy: sensitive admin endpoints behind extra network or MFA requirements

Once rules grow, a dedicated policy object is usually clearer than a pile of inline dependency closures.

## 8) WebSocket auth resembles HTTP auth, but is not identical

WebSockets usually authenticate on connect, then may authorize each message separately.

- validate token or cookie on connect
- apply message-level authorization for room joins or commands
- clean up on disconnect
- define invalid-token close codes

So the question "may this connection open?" is separate from "may this message be sent?".

## 9) Errors and logging are part of security design

- invalid or missing credentials: `401 Unauthorized`
- authenticated but not allowed: `403 Forbidden`
- avoid leaking too much account-existence detail in error messages
- log auth failures structurally, but never log raw secrets

Rate limiting, audit logging, and suspicious-activity monitoring belong right after the auth boundary.

## 10) Practical checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Did you separate authn from authz?</h3>
    <p>Credential parsing and policy checks should not be one tangled function.</p>
  </div>
  <div class="check-card">
    <h3>Did you distinguish cookie and token threat models?</h3>
    <p>Browser, cross-origin, CSRF, and XSS exposure differ.</p>
  </div>
  <div class="check-card">
    <h3>Do you have a revoke and rotation story?</h3>
    <p>JWTs still need forced logout and key rotation planning.</p>
  </div>
  <div class="check-card">
    <h3>Did you include WebSocket auth?</h3>
    <p>Do not secure only HTTP routes and leave real-time paths behind.</p>
  </div>
</div>

## Good companion chapters in this repository

1. [Request/Response Modeling](/en/fastapi/request-response-modeling)
2. [Background Tasks and Offloading](/en/fastapi/background-tasks-and-offloading)
3. [WebSocket Practical Patterns](/en/fastapi/websocket-practical-patterns)
4. [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings)

For runnable code, see `examples/fastapi_security_auth_lab.py`.

## Official References

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette Authentication](https://www.starlette.io/authentication/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [RFC 7519 - JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
