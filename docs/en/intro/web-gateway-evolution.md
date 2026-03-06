# Web Gateway Evolution: CGI, WSGI, ASGI

<p class="lead">To understand Python web frameworks properly, it helps to look at the server/application contract before looking at FastAPI or Django. CGI, WSGI, and ASGI are not just acronyms. They describe how Python web systems changed as traffic models, runtime expectations, and protocol needs evolved.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: CGI was the simplest process-per-request model. WSGI standardized long-lived synchronous HTTP apps and unified the Python web ecosystem. ASGI expanded the contract around `scope`, `receive`, and `send` so that async I/O, WebSockets, lifespan, and streaming could fit into one event-driven interface.</p>
</div>

## Why a gateway interface exists at all

- The server owns sockets, connection handling, timeouts, worker processes, and proxy behavior.
- The application owns routing, validation, templates, business rules, and persistence orchestration.
- A stable contract between the two is what makes frameworks portable across servers and servers reusable across frameworks.

<MermaidDiagram
  caption="Python web interfaces evolved by redefining the server/application boundary for each era."
  chart="flowchart LR; A[&quot;CGI&quot;] --> B[&quot;WSGI&quot;]; B --> C[&quot;ASGI&quot;]; A --> D[&quot;Process per request&quot;]; B --> E[&quot;Sync request and response&quot;]; C --> F[&quot;Async connection and events&quot;];"
/>

## 1) CGI: simple, but expensive per request

CGI(Common Gateway Interface) let a web server launch an external program for each request and exchange data through environment variables plus standard input and output.

### Why it made sense first

- It was simple to implement.
- It kept the server and application loosely coupled.
- The mental model of "one HTTP request, one program execution" was easy to understand.

### Why it stopped scaling well

- Starting a new process for every request is expensive.
- Reusing DB connections, caches, or initialized application state is difficult.
- Long-lived connections and streaming-style protocols do not fit naturally.

CGI opened the door to dynamic web apps, but the process model was too costly for a growing framework ecosystem.

## 2) WSGI: the common contract that unified Python web apps

WSGI(Web Server Gateway Interface), defined in PEP 3333, gave Python web apps one standard callable shape:

```py
def application(environ, start_response):
    ...
```

### What WSGI solved

- Apps could run inside long-lived workers instead of starting a new process per request.
- Servers and frameworks could interoperate cleanly.
- Middleware composition became a stable pattern.
- The ecosystem moved away from server-specific integration APIs.

### Why WSGI fit its era

- Most web applications were synchronous request/response HTTP services.
- Process and thread worker models were acceptable and well understood.
- The main ecosystem need was portability and standardization, not async protocol coverage.

### Where WSGI started to strain

- WebSockets and other long-lived bidirectional connections
- SSE, streaming responses, and long polling
- Async database and HTTP clients
- Standardized startup and shutdown semantics

WSGI is excellent for synchronous HTTP request/response handling, but it is not shaped for connection-oriented event flows.

## 3) ASGI: standardizing connections and events, not just requests

ASGI(Asynchronous Server Gateway Interface) is not merely "async WSGI". It broadens the interface so applications can react to connection-scoped events.

```py
async def app(scope, receive, send):
    ...
```

### What ASGI adds

- `scope`: static metadata for the connection
- `receive`: events coming from the server into the application
- `send`: events emitted from the application back to the server
- protocol types such as `http`, `websocket`, and `lifespan`

### Why ASGI became necessary

- `asyncio` became the standard concurrency foundation in Python.
- Modern services needed one contract for HTTP, WebSockets, lifespan hooks, and streaming.
- The natural runtime unit became a connection plus event flow, not only a one-shot HTTP request.

ASGI sits above raw socket programming, but below framework-level routing and validation. That makes it the right place to standardize runtime interactions for modern Python web apps.

## CGI, WSGI, and ASGI in one table

| Interface | Main unit | Typical shape | Best fit | Main limitation |
| --- | --- | --- | --- | --- |
| CGI | process | env vars plus stdin/stdout | early dynamic web | process cost per request |
| WSGI | synchronous request/response | `application(environ, start_response)` | sync HTTP web apps | websockets, async, lifespan |
| ASGI | connection and events | `async def app(scope, receive, send)` | async HTTP, websockets, streaming | requires more runtime understanding |

## Practical mental model

- CGI is an execution interface.
- WSGI is a synchronous HTTP request interface.
- ASGI is a connection-and-events interface.

For FastAPI, the critical point is not that "FastAPI is fast". It is that FastAPI is an ASGI application and an ASGI server such as Uvicorn is what actually runs it.

## Where to read next in this repository

1. [ASGI and Uvicorn](/en/fastapi/asgi-and-uvicorn)
2. [Lifespan and Testing](/en/fastapi/lifespan-and-testing)
3. [Background Tasks and Offloading](/en/fastapi/background-tasks-and-offloading)

For runnable intuition, pair this chapter with `examples/asgi_lifecycle_lab.py`.

## Official References

- [PEP 3333 - WSGI for Python 3](https://peps.python.org/pep-3333/)
- [ASGI Specification](https://asgi.readthedocs.io/en/latest/specs/main.html)
- [ASGI Introduction](https://asgi.readthedocs.io/en/latest/introduction.html)
- [PEP 3156 - asyncio](https://peps.python.org/pep-3156/)
