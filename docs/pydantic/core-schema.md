# Core Schema

<p class="lead">Pydantic v2의 핵심은 `BaseModel`이 직접 validation을 수행하는 것이 아니라, annotation과 제약을 바탕으로 core schema라는 중간 표현을 만들고, `pydantic-core`가 그 schema를 실행한다는 점이다. 이 구조를 이해하면 Pydantic이 왜 빠르고, 왜 `TypeAdapter`가 중요한지, 왜 custom type 확장 방식이 그런 모양인지 설명할 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: core schema는 "Python 타입 힌트와 제약을 pydantic-core가 실행할 수 있는 형태로 컴파일한 그래프"다. `BaseModel`, `Annotated`, field 제약, validator, `TypeAdapter`는 모두 결국 이 schema를 만들고 소비하는 서로 다른 입구다.</p>
</div>

## 먼저 흐름을 그림으로 잡기

<MermaidDiagram
  caption="Pydantic은 annotation을 바로 검증하지 않는다. 먼저 core schema를 만들고, 그 schema를 pydantic-core의 validator/serializer가 실행한다."
  chart="flowchart LR; A[Python annotations and constraints] --> B[Pydantic schema builder]; B --> C[Core schema graph]; C --> D[SchemaValidator in pydantic-core]; C --> E[SchemaSerializer in pydantic-core]; D --> F[Python objects or ValidationError]; E --> G[dict, JSON-ready output, JSON schema];"
/>

## 왜 중요한가

- `BaseModel`이 아닌 타입도 `TypeAdapter`로 같은 엔진에 태울 수 있는 이유를 설명할 수 있다.
- validator, field constraint, `Annotated` metadata가 어떻게 합쳐지는지 이해할 수 있다.
- custom type 확장이나 framework integration을 볼 때 "마법"이 아니라 schema 생성 단계로 이해하게 된다.

## core schema를 가장 짧게 체감하는 코드

```py
from typing import Annotated

from pydantic import AfterValidator, BaseModel, TypeAdapter


def positive(value: int) -> int:
    if value <= 0:
        raise ValueError("positive only")
    return value


PositiveInt = Annotated[int, AfterValidator(positive)]


class LineItem(BaseModel):
    qty: PositiveInt


adapter = TypeAdapter(list[PositiveInt])

print(LineItem.model_validate({"qty": "3"}))
print(adapter.validate_python(["1", 2, 3]))
print("adapter core schema type:", adapter.core_schema["type"])
```

<p class="code-caption">`LineItem`과 `TypeAdapter(list[PositiveInt])`는 다른 입구처럼 보이지만, 둘 다 내부적으로 core schema를 만들고 `pydantic-core` validator를 사용한다. 위 예제의 `adapter.core_schema["type"]`은 최상위 schema가 `list`임을 보여준다.</p>

## 무엇이 schema에 들어가나

- 기본 타입 정보: `int`, `str`, `list[T]`, `dict[K, V]`
- 구조 정보: model field, union, tagged/discriminated union
- 제약 정보: min/max, regex, length, strict 여부
- hook 정보: before/after/wrap validator, serializer
- metadata: `Annotated`로 전달되는 추가 정보

## 왜 `Annotated`가 중요한가

Pydantic v2에서는 많은 확장 포인트가 `Annotated`를 통해 schema에 들어간다. 즉, typing 정보와 runtime validation metadata가 같은 선언 위치에 모이게 된다.

```py
from typing import Annotated
from pydantic import Field, TypeAdapter

UserId = Annotated[int, Field(gt=0, description="database primary key")]

adapter = TypeAdapter(UserId)
print(adapter.validate_python("10"))
```

## 언제 core schema를 직접 의식해야 하나

<div class="doc-checklist">
  <div class="check-card">
    <h3>커스텀 타입</h3>
    <p>기본 모델 선언으로 표현되지 않는 입력 규칙을 타입 수준에서 재사용하고 싶을 때.</p>
  </div>
  <div class="check-card">
    <h3>TypeAdapter 재사용</h3>
    <p>모델 클래스 없이 리스트, TypedDict, union 같은 임의 타입을 빠르게 검증하고 싶을 때.</p>
  </div>
  <div class="check-card">
    <h3>프레임워크 통합</h3>
    <p>annotation을 읽어 validation 엔진이나 schema를 만드는 도구를 작성할 때.</p>
  </div>
  <div class="check-card">
    <h3>성능 감각</h3>
    <p>validation 로직이 매 입력마다 Python 함수를 순회하는 것이 아니라, 미리 구성된 schema graph를 실행한다는 점을 이해할 때.</p>
  </div>
</div>

## 공식 자료

- [Pydantic Architecture](https://docs.pydantic.dev/latest/internals/architecture/)
- [Type Adapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
