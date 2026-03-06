# Client Protocol and Reconnect

<p class="lead">If a WebSocket project starts with "as long as it connects, we're fine", the protocol usually becomes the painful part later. Without a clear first-message shape, protocol version, room join contract, event IDs, resume cursors, and close code policy, reconnect quickly turns into duplication, loss, and compatibility problems.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: treat WebSocket as an application protocol, not just as an open socket. Use envelopes such as `server.hello`, `client.join`, `chat.message`, and `server.error`, and make `protocol_version`, `session_id`, `event_id`, and `resume_from` explicit. Reconnect is not just retrying the transport. It is deciding where to resume the event stream.</p>
</div>

## Recommended baseline flow

<MermaidDiagram
  caption="In practice, the first frames and the reconnect resume contract matter more than the raw socket open itself."
  chart="sequenceDiagram; participant C as Client; participant S as Server; C->>S: WebSocket connect with token; S->>C: server.hello(session_id, protocol_version); C->>S: client.join(room_id, resume_from); S->>C: room.joined; S->>C: replay missed events after resume_from; C->>S: chat.send(text); S->>C: chat.message(event_id, text);"
/>

## 1) Make the protocol explicit from the first frame

Useful envelope fields:

- `kind`
- `protocol_version`
- `session_id`
- `room_id`
- `event_id`
- `correlation_id`
- `payload`

Not every field needs to appear on every frame, but the envelope rules should exist.

### Example

```json
{"kind":"server.hello","protocol_version":1,"session_id":"session-neo"}
{"kind":"client.join","room_id":"core","resume_from":41}
{"kind":"chat.message","room_id":"core","event_id":42,"sender":"neo","text":"hello"}
```

## 2) Why `server.hello` is useful

`server.hello` is the agreement that "the connection is open, and we are now speaking this protocol version".

Good contents:

- `protocol_version`
- `session_id`
- server timestamp
- capability flags

Benefits:

- the client can detect protocol mismatch early
- reconnect can track whether it is re-entering the same logical session shape
- later feature flags have a natural place to live

## 3) Make room join idempotent

Connect and room membership are not the same step.

- connect is transport and auth
- join is application-level membership

A clean pattern is:

- `server.hello` after connect
- client sends `client.join`
- server replies with `room.joined`

That makes reconnect easier because repeating `client.join` becomes safe by design.

## 4) Reconnect is really about `resume_from`

Retrying the socket alone easily creates duplicates or gaps.

Typical ingredients:

- server-generated increasing `event_id`
- the last `event_id` the client saw
- reconnect with `resume_from=<last_seen>`

```json
{"kind":"client.join","room_id":"core","resume_from":41}
```

The server then either:

- replays events after 41
- or tells the client to fetch a fresh snapshot if replay is unavailable

## 5) When replay is unavailable, HTTP snapshot usually becomes the fallback

If the system only has live fan-out, such as Redis pub/sub with no durable history, websocket reconnect alone cannot restore missed events. A common model is:

1. refetch the latest HTTP snapshot
2. continue the websocket stream from that point onward

That means websocket reconnect design is often coupled with an HTTP read model.

## 6) Client backoff should be treated as part of the protocol

Useful defaults:

- exponential backoff
- jitter
- a maximum delay cap
- different handling for auth failure versus transient failure

Separate these cases:

- invalid token: do not retry immediately
- transient network failure: retry with backoff
- protocol mismatch: prompt refresh or app update

## 7) Separate close codes from error frames

- a close code is a connection-level signal
- a `server.error` frame is an application-level signal

Using both makes it easier to distinguish:

- when the connection should close
- versus when the client can recover within the same connection

## Recommended baseline

| Concern | Recommended default |
| --- | --- |
| protocol shape | `kind`-based envelope |
| handshake | start with `server.hello` |
| membership | separate `client.join` and `room.joined` |
| replay | `event_id` plus `resume_from` |
| reconnect | backoff plus jitter |
| no replay available | fall back to an HTTP snapshot |

## Repository examples

- `examples/websocket_client_protocol_reconnect_lab.py`
- `examples/websocket_auth_and_rooms_lab.py`

## Companion chapters

1. [WebSocket Practical Patterns](/en/fastapi/websocket-practical-patterns)
2. [Redis Pub/Sub and Multi-worker Broadcast](/en/fastapi/websocket-redis-pubsub)
3. [WebSockets, Streaming, and Middleware](/en/fastapi/websockets-streaming-and-middleware)

## Official References

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Starlette WebSockets](https://www.starlette.io/websockets/)
- [RFC 6455 - The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
