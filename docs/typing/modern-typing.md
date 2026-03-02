# Modern Typing

<p class="lead">요즘 Python 회사에서 typing은 선택사항이 아니라 기본 전제인 경우가 많다. 특히 3.10 이후 문법 개선 덕분에 typing은 더 이상 장황한 보조 문법이 아니라, 코드 자체를 읽기 좋게 만드는 설계 도구가 되었다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 현대 Python typing의 핵심은 `X | Y`, `type` alias, `Annotated`, `Literal`, `Self`, `Never`, built-in generic syntax처럼 "코드 모양 자체를 더 읽기 좋게 만드는 도구"들이다.</p>
</div>

## 빠르게 보는 핵심 문법

| 기능 | 왜 중요한가 | 예시 |
| --- | --- | --- |
| `X | Y` | `Union[X, Y]`보다 훨씬 읽기 좋다 | `str | None` |
| `type` alias | alias 선언 의도를 더 분명히 드러낸다 | `type UserId = int` |
| `Annotated` | 타입과 metadata를 한 자리에 둔다 | `Annotated[int, Query(gt=0)]` |
| `Literal` | 허용 값 집합을 명시한다 | `Literal["draft", "published"]` |
| `Self` | fluent API와 classmethod return을 깔끔하게 만든다 | `def with_name(self, ...) -> Self` |
| `Never` | 도달 불가능한 흐름이나 종료 함수 시그니처를 표현한다 | `def fail() -> Never` |
| built-in generics | `list[int]` 같은 표기가 기본이 됐다 | `dict[str, int]` |

## 실전 예제

```py
from typing import Annotated, Literal, Never, Self


type UserId = int
type Status = Literal["draft", "published"]


class Article:
    def __init__(self, title: str, status: Status = "draft") -> None:
        self.title = title
        self.status = status

    def publish(self) -> Self:
        self.status = "published"
        return self


def fail(message: str) -> Never:
    raise RuntimeError(message)


PageSize = Annotated[int, "1..100 constraint lives here"]
```

## `Annotated`는 타입과 metadata의 만남이다

- 타입 체커는 주로 앞의 타입 부분을 본다.
- FastAPI, Pydantic 같은 프레임워크는 뒤의 metadata도 소비할 수 있다.
- 그래서 `Annotated`는 "정적 타입"과 "런타임 소비 정보"가 만나는 중요한 접점이다.

## alias를 언제 두는 게 좋은가

<div class="doc-checklist">
  <div class="check-card">
    <h3>도메인 의미가 생길 때</h3>
    <p>`UserId`, `OrderNumber`, `Slug`처럼 단순 타입보다 의미가 중요한 경우 alias가 가독성을 높인다.</p>
  </div>
  <div class="check-card">
    <h3>복잡한 union을 반복할 때</h3>
    <p>여러 곳에서 쓰는 긴 type expression은 alias로 빼는 편이 API 문맥을 더 잘 드러낸다.</p>
  </div>
  <div class="check-card">
    <h3>metadata까지 재사용할 때</h3>
    <p>`Annotated` alias로 validation metadata와 타입을 함께 재사용할 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>너무 이른 alias는 피한다</h3>
    <p>한 번만 쓰는 단순 타입까지 alias로 감싸면 오히려 읽기 어려워진다.</p>
  </div>
</div>

## 공식 자료

- [typing](https://docs.python.org/3/library/typing.html)
- [PEP 695: Type Parameter Syntax](https://peps.python.org/pep-0695/)
