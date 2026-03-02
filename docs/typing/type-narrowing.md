# Type Narrowing

<p class="lead">실무 typing의 품질은 선언보다 narrowing에서 많이 갈린다. 타입을 넓게 받고 안전한 분기 후에 좁히는 설계가 자연스럽지 않으면, 코드베이스 전체가 `Any`나 캐스팅에 기대기 쉬워진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: narrowing은 "런타임 검사를 정적 타입 정보로 연결하는 기술"이다. `isinstance`, `match`, `TypeGuard`, `TypeIs`를 제대로 쓰면 cast를 크게 줄일 수 있다.</p>
</div>

## narrowing 그림

<MermaidDiagram
  caption="넓은 입력 타입을 받고, 런타임 검사 결과를 통해 더 좁은 타입으로 다루는 것이 narrowing의 핵심이다."
  chart="flowchart LR; A[broad input type] --> B[runtime check]; B --> C[narrowed true branch]; B --> D[narrowed false branch];"
/>

## `TypeGuard`와 `TypeIs` 차이

```py
from typing import TypeGuard, TypeIs


def is_str_list(values: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(value, str) for value in values)


def is_int(value: int | str) -> TypeIs[int]:
    return isinstance(value, int)
```

<p class="code-caption">`TypeGuard`는 "이 복잡한 구조를 더 구체적인 타입으로 볼 수 있다"를 표현할 때 유용하고, `TypeIs`는 `isinstance`에 가까운 타입 판별을 더 엄격한 의미로 표현할 때 유용하다.</p>

## `match`도 narrowing과 연결된다

```py
def describe(value: int | str | None) -> str:
    match value:
        case int():
            return "int"
        case str():
            return "str"
        case None:
            return "none"
```

## truthiness narrowing 한계

- `if value:`는 빈 문자열, 0, 빈 리스트, `None`을 한꺼번에 걸러버린다.
- 그래서 "없음"과 "비어 있음"을 구분해야 할 때 truthiness만 믿으면 타입과 의미가 같이 흐려진다.

## 실전 연결

- input validation helper
- discriminator 기반 분기
- API payload parsing

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>cast보다 narrowing 우선</h3>
    <p>가능하면 런타임 검사를 타입 체커가 이해할 수 있는 형태로 만들어 cast를 줄인다.</p>
  </div>
  <div class="check-card">
    <h3>truthiness 남용 금지</h3>
    <p>빈 값과 없는 값을 구분해야 한다면 명시적 비교가 더 안전하다.</p>
  </div>
  <div class="check-card">
    <h3>TypeGuard와 TypeIs를 구분</h3>
    <p>구조 변환에 가까운 narrowing은 `TypeGuard`, 진짜 타입 판별은 `TypeIs`가 더 맞는다.</p>
  </div>
  <div class="check-card">
    <h3>discriminator를 명시한다</h3>
    <p>union payload를 다룰 때는 `kind`, `type` 같은 구분자를 두는 편이 match와 narrowing 모두에 유리하다.</p>
  </div>
</div>

## 공식 자료

- [typing.TypeGuard](https://docs.python.org/3/library/typing.html#typing.TypeGuard)
- [typing.TypeIs](https://docs.python.org/3/library/typing.html#typing.TypeIs)
