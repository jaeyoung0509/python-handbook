# Dataclasses

<p class="lead">`dataclass`는 Python에서 "가벼운 구조체"를 가장 자연스럽게 만드는 도구다. 단순히 `__init__`를 자동 생성하는 편의 기능으로만 보면 절반만 이해한 셈이고, 실제로는 값 객체, 내부 command payload, 설정 객체, 패턴 매칭용 노드 표현을 아주 깔끔하게 만들 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: dataclass는 validation 엔진이나 ORM 대체재가 아니라, Python annotation을 바탕으로 `__init__`, `__repr__`, `__eq__` 같은 보일러플레이트를 줄여 주는 값 중심 도구다. `frozen=True`, `slots=True`, `kw_only=True`, `default_factory`, `__post_init__` 조합을 익히면 실무 활용도가 매우 높다.</p>
</div>

## 먼저 mental model부터

<MermaidDiagram
  caption="dataclass는 클래스 자체를 다른 모델로 바꾸는 것이 아니라, 기존 클래스에 생성자와 비교/표현 메서드를 붙여 값 중심 객체로 쓰기 쉽게 만든다."
  chart="flowchart LR; A[&quot;Annotated class body&quot;] --> B[&quot;@dataclass decorator&quot;]; B --> C[&quot;Generated __init__, __repr__, __eq__&quot;]; B --> D[&quot;Optional frozen, slots, kw_only, match_args&quot;]; C --> E[&quot;Value object or internal payload&quot;];"
/>

## 언제 매우 잘 맞나

- 값 객체(value object)
- 내부 command / query payload
- 설정 객체
- 패턴 매칭 대상 노드
- 테스트용 fixture 데이터 묶음

## 언제 억지로 쓰지 않는 편이 좋나

- 외부 입력 validation이 중요한 API boundary
- 복잡한 lifecycle과 lazy loading을 가진 ORM entity
- 동적 속성 주입이 많은 프레임워크 객체

## 가장 자주 쓰는 안전한 조합

```py
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True, kw_only=True)
class RetryPolicy:
    max_attempts: int
    base_delay_ms: int = 100
    retry_on: tuple[str, ...] = field(default_factory=lambda: ("timeout", "busy"))
```

<p class="code-caption">`frozen=True`는 불변 값 객체처럼 쓰고 싶을 때 좋고, `slots=True`는 메모리와 attribute shape를 더 명확하게 만든다. `kw_only=True`는 인자 위치 실수를 줄여서 설정 객체나 command payload에 특히 잘 맞는다.</p>

## `default_factory`를 반드시 기억해야 하는 이유

```py
from dataclasses import dataclass, field


@dataclass
class Batch:
    job_id: str
    items: list[str] = field(default_factory=list)
```

- mutable default를 `[]`로 직접 두면 인스턴스 간 상태가 섞일 수 있다.
- dataclass 공식 문서도 mutable default에는 `default_factory`를 쓰도록 강하게 안내한다.

## `__post_init__()`는 normalization 지점이다

```py
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if "@" not in normalized:
            raise ValueError("invalid email address")
        object.__setattr__(self, "value", normalized)
```

`__post_init__()`는 생성 후 정규화나 field 간 일관성 검사에 좋다. 다만 이것을 "전체 입력 validation 프레임워크"처럼 키우기 시작하면 Pydantic이나 별도 validation boundary가 더 맞는 경우가 많다.

## dataclass와 pattern matching은 잘 맞는다

- dataclass는 기본적으로 `__match_args__`를 생성할 수 있다.
- 그래서 내부 AST 노드나 command 타입을 `match/case`로 분기하기 좋다.
- 3.10의 `match_args`, `kw_only` 옵션도 이 흐름과 연결된다.

## 실무에서 자주 추천하는 규칙

| 상황 | 추천 |
| --- | --- |
| 내부 값 객체 | `frozen=True`, 필요하면 `slots=True` |
| 설정 / command payload | `kw_only=True` 적극 사용 |
| list/dict/set 필드 | `default_factory` 사용 |
| API boundary | dataclass만으로 끝내지 말고 validation 계층 분리 |
| ORM entity | dataclass와 ORM을 억지로 한 몸으로 만들지 않기 |

## 흔한 실수

- mutable default를 직접 둔다.
- dataclass를 request validation 도구처럼 사용한다.
- 불변 객체가 필요한데 `frozen=True` 없이 값 객체처럼 취급한다.
- ORM model, dataclass DTO, Pydantic schema를 하나로 합치려 한다.

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>값 객체인가</h3>
    <p>행동보다 데이터 구조와 equality가 더 중요하면 dataclass가 잘 맞는다.</p>
  </div>
  <div class="check-card">
    <h3>mutable default를 피했는가</h3>
    <p>list, dict, set 필드는 `default_factory`가 기본이다.</p>
  </div>
  <div class="check-card">
    <h3>validation 경계를 구분했는가</h3>
    <p>외부 입력을 다루는 boundary라면 dataclass 하나로 모든 검증을 해결하려 하지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>keyword-only가 더 안전한가</h3>
    <p>설정 객체나 긴 payload는 `kw_only=True`로 위치 인수 실수를 줄이는 편이 낫다.</p>
  </div>
</div>

## 공식 자료

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [PEP 557](https://peps.python.org/pep-0557/)
