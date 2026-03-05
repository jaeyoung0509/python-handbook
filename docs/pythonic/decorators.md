# Decorators

<p class="lead">decorator는 Python에서 확장을 가장 싸게 붙일 수 있는 도구다. 하지만 wrapper를 잘못 만들면 signature, docstring, type information, 디버깅 가능성을 한꺼번에 망칠 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 좋은 decorator는 behavior만 추가하고, 원래 함수의 signature와 metadata는 최대한 보존한다. `functools.wraps`와 `ParamSpec`은 선택이 아니라 거의 기본값에 가깝다.</p>
</div>

## decorator가 개입하는 위치

<MermaidDiagram
  caption="decorator는 원래 callable을 받아 새로운 callable 또는 class를 돌려주는 구조다. 핵심은 원래 contract를 얼마나 보존하느냐다."
  chart="flowchart LR; A[&quot;original function&quot;] --> B[&quot;decorator&quot;]; B --> C[&quot;wrapper function&quot;]; C --> D[&quot;extra behavior before or after call&quot;]; D --> E[&quot;delegate to original&quot;];"
/>

## `wraps`와 `ParamSpec`를 같이 쓰는 기본형

```py
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def traced(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            print(f"[{name}] before", func.__name__)
            result = func(*args, **kwargs)
            print(f"[{name}] after", func.__name__)
            return result

        return wrapper

    return decorator


@traced("calc")
def add(x: int, y: int) -> int:
    return x + y


print(add(1, 2))
print(add.__name__)
```

<p class="code-caption">`wraps()`는 `__name__`, `__doc__`, `__wrapped__` 같은 metadata를 보존하고, `ParamSpec`은 wrapper가 원래 함수의 호출 시그니처를 타입 수준에서 이어받게 해준다.</p>

## class decorator와 function decorator는 쓰임이 다르다

- function decorator: 호출 전후 behavior 추가, tracing, caching, retry
- class decorator: class object 후처리, 등록, 속성 수정
- metaclass보다 가벼운 class-level hook이 필요할 때 class decorator가 유용하다

## decorator 남용 패턴

<div class="doc-checklist">
  <div class="check-card">
    <h3>너무 많은 implicit behavior</h3>
    <p>retry, logging, tracing, auth, transaction을 여러 decorator로 겹치면 디버깅이 급격히 어려워진다.</p>
  </div>
  <div class="check-card">
    <h3>metadata 손실</h3>
    <p>`wraps()`를 쓰지 않으면 introspection, 문서화, framework integration이 깨지기 쉽다.</p>
  </div>
  <div class="check-card">
    <h3>type 정보 손실</h3>
    <p>`Callable[..., Any]`로 대충 잡으면 decorator가 많은 코드베이스에서 타입 품질이 빠르게 나빠진다.</p>
  </div>
  <div class="check-card">
    <h3>stateful decorator 복잡성</h3>
    <p>내부에 mutable state를 오래 쥐는 decorator는 concurrency와 test isolation 문제를 만들기 쉽다.</p>
  </div>
</div>

## 실전 연결

- FastAPI route decorator
- dependency injection helper
- logging / tracing / caching decorator

## 공식 자료

- [functools.wraps](https://docs.python.org/3/library/functools.html#functools.wraps)
- [typing.ParamSpec](https://docs.python.org/3/library/typing.html#typing.ParamSpec)
