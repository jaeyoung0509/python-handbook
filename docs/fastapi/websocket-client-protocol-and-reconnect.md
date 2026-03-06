# Client Protocol과 Reconnect

<p class="lead">WebSocket이 "연결만 되면 된다"는 생각으로 시작하면 나중에 가장 크게 아픈 부분이 protocol이다. connect 후 첫 메시지 구조, protocol version, room join 방식, event id, resume cursor, close code 기준이 없으면 reconnect 시 중복/누락/호환성 문제가 한꺼번에 터진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: WebSocket도 API처럼 프로토콜을 설계해야 한다. `server.hello`, `client.join`, `chat.message`, `server.error` 같은 envelope를 두고, `protocol_version`, `session_id`, `event_id`, `resume_from`을 명시하면 reconnect와 resume가 훨씬 안정적이다. 재연결은 단순 retry가 아니라 "어디부터 다시 이어받을지"를 정하는 문제다.</p>
</div>

## 추천 기본 흐름

<MermaidDiagram
  caption="실전에서는 connect 뒤 첫 메시지 구조와 reconnect resume 규약이 중요하다."
  chart="sequenceDiagram; participant C as Client; participant S as Server; C->>S: WebSocket connect with token; S->>C: server.hello(session_id, protocol_version); C->>S: client.join(room_id, resume_from); S->>C: room.joined; S->>C: replay missed events after resume_from; C->>S: chat.send(text); S->>C: chat.message(event_id, text);"
/>

## 1) 첫 프레임부터 protocol을 명시한다

최소 envelope 필드:

- `kind`
- `protocol_version`
- `session_id`
- `room_id`
- `event_id`
- `correlation_id`
- `payload`

모든 필드를 모든 메시지에 다 넣을 필요는 없지만, envelope 기준은 있어야 한다.

### 예시

```json
{"kind":"server.hello","protocol_version":1,"session_id":"session-neo"}
{"kind":"client.join","room_id":"core","resume_from":41}
{"kind":"chat.message","room_id":"core","event_id":42,"sender":"neo","text":"hello"}
```

## 2) `server.hello`를 두는 이유

`server.hello`는 "연결은 됐고, 지금부터 이 버전의 프로토콜로 말하자"는 합의다.

여기에 넣기 좋은 것:

- `protocol_version`
- `session_id`
- server timestamp
- capability flags

장점:

- 클라이언트가 protocol mismatch를 빨리 감지한다.
- reconnect 시 동일 세션인지 추적하기 쉽다.
- 나중에 기능 플래그를 추가해도 자리가 있다.

## 3) room join은 idempotent해야 한다

connect와 room membership은 다른 단계다.

- connect는 transport/auth 단계
- join은 application membership 단계

그래서 좋은 패턴은:

- 연결 직후 `server.hello`
- 클라이언트가 `client.join`
- 서버가 `room.joined`

이렇게 나누는 것이다. 그러면 reconnect 후 같은 `client.join`을 여러 번 보내도 안전하게 처리하기 쉬워진다.

## 4) reconnect는 `resume_from`이 핵심이다

단순 재연결만 있으면 중복/누락이 쉽게 생긴다.

그래서 보통:

- 서버 이벤트마다 증가하는 `event_id`
- 클라이언트가 마지막으로 본 `event_id`
- reconnect 후 `resume_from=<last_seen>`

를 사용한다.

```json
{"kind":"client.join","room_id":"core","resume_from":41}
```

서버는:

- 42 이후 이벤트를 replay해주거나
- replay 불가면 "snapshot을 다시 받아라"는 error를 준다

## 5) replay가 안 되면 HTTP snapshot 경로가 필요하다

Redis pub/sub처럼 history가 없는 fan-out만 쓰는 경우, websocket reconnect만으로는 놓친 이벤트를 복원할 수 없다. 이때는 보통:

1. HTTP로 최신 snapshot을 다시 가져오고
2. 그 시점 이후 websocket event를 이어받는다

라는 2-step 모델을 둔다.

즉, websocket reconnect 설계는 보통 HTTP read model과 같이 봐야 한다.

## 6) client backoff도 protocol 일부로 본다

좋은 기본값:

- exponential backoff
- jitter
- 최대 대기 시간 상한
- auth 실패와 일시 장애를 구분

실무에서 구분할 것:

- 잘못된 token: 즉시 재시도하지 않음
- 일시 네트워크 문제: backoff 후 재시도
- protocol mismatch: 앱 업데이트 또는 hard refresh 유도

## 7) close code와 error frame을 분리한다

- close code는 연결 레벨 신호다.
- `server.error` frame은 애플리케이션 레벨 신호다.

둘을 같이 쓰면:

- 연결 자체를 끊어야 하는가
- 아니면 같은 연결에서 recover 가능한가

를 구분하기 쉬워진다.

## 추천 기본 패턴

| 관심사 | 추천 |
| --- | --- |
| protocol shape | `kind` 기반 envelope |
| handshake | `server.hello` 먼저 |
| membership | `client.join` / `room.joined` 분리 |
| replay | `event_id` + `resume_from` |
| reconnect | backoff + jitter |
| replay 불가 시 | HTTP snapshot fallback |

## 이 저장소 예제

- `examples/websocket_client_protocol_reconnect_lab.py`
- `examples/websocket_auth_and_rooms_lab.py`

## 같이 읽으면 좋은 페이지

1. [WebSocket 실전 패턴](/fastapi/websocket-practical-patterns)
2. [Redis Pub/Sub과 Multi-worker Broadcast](/fastapi/websocket-redis-pubsub)
3. [WebSocket, Streaming, Middleware](/fastapi/websockets-streaming-and-middleware)
4. [계약 진화와 지속가능한 CD](/playbooks/contract-evolution-and-sustainable-cd)

## 공식 자료

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette WebSockets](https://www.starlette.io/websockets/)
- [RFC 6455 - The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
