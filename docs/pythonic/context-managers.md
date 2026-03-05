# Context Managers

<p class="lead">context manager는 Python에서 자원과 경계를 표현하는 가장 Pythonic한 도구다. 파일, DB session, lock, timeout, lifespan, test fixture cleanup까지 전부 "들어갈 때 준비하고, 나올 때 정리한다"는 같은 모델로 설명할 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: `with` 문은 단순 문법 설탕이 아니라 `try/finally`를 구조적으로 고정하는 장치다. resource scope, transaction scope, lifespan scope를 코드 형태로 명확하게 만드는 데 가장 좋다.</p>
</div>

## `with`의 실행 모델

<MermaidDiagram
  caption="context manager는 들어갈 때 자원을 준비하고, 블록이 정상 종료든 예외 종료든 나갈 때 정리를 보장한다."
  chart="flowchart LR; A[&quot;enter with block&quot;] --> B[&quot;__enter__ or async __aenter__&quot;]; B --> C[&quot;body execution&quot;]; C --> D[&quot;normal exit or exception&quot;]; D --> E[&quot;__exit__ or async __aexit__&quot;];"
/>

## 가장 단순한 class 기반 context manager

```py
class SessionScope:
    def __enter__(self) -> str:
        print("open resource")
        return "session"

    def __exit__(self, exc_type, exc, tb) -> bool:
        print("close resource")
        return False


with SessionScope() as session:
    print("using", session)
```

## `contextlib`를 쓰면 더 깔끔할 때가 많다

```py
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def transaction_scope() -> Iterator[str]:
    print("begin")
    try:
        yield "tx"
        print("commit")
    except Exception:
        print("rollback")
        raise
    finally:
        print("close")


with transaction_scope() as tx:
    print("inside", tx)
```

<p class="code-caption">resource lifecycle이 명확한 경우에는 class보다 `@contextmanager`가 더 짧고 읽기 좋다. 반대로 상태를 많이 들고 있거나 재사용 가능한 객체 모델이 필요하면 class 기반이 낫다.</p>

## async context manager가 중요한 이유

```py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan_scope() -> AsyncIterator[str]:
    print("startup")
    try:
        yield "app-state"
    finally:
        print("shutdown")
```

## 실전 연결

- DB session scope
- FastAPI lifespan
- 테스트 fixture와 cleanup

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>scope를 코드로 드러낸다</h3>
    <p>열고 닫는 자원이 있으면 `with`/`async with`로 경계를 명시하는 편이 좋다.</p>
  </div>
  <div class="check-card">
    <h3>예외 경로를 정상 경로만큼 중요하게 본다</h3>
    <p>commit과 rollback, startup과 shutdown, acquire와 release를 같이 설계해야 한다.</p>
  </div>
  <div class="check-card">
    <h3>class vs helper를 구분한다</h3>
    <p>재사용 가능한 자원 객체가 필요하면 class, 단순 lifecycle helper면 `contextlib`가 더 낫다.</p>
  </div>
  <div class="check-card">
    <h3>async 자원은 async context로</h3>
    <p>네트워크 client, async DB session, lifespan state는 `async with`로 관리하는 편이 안전하다.</p>
  </div>
</div>

## 공식 자료

- [contextlib](https://docs.python.org/3/library/contextlib.html)
- [The with statement](https://docs.python.org/3/reference/compound_stmts.html#the-with-statement)
