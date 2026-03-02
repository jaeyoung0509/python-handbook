# BaseModel vs TypeAdapter

<p class="lead">Pydantic v2에서는 "입력을 검증하려면 무조건 `BaseModel`을 하나 만든다"는 습관을 버릴 필요가 있다. `BaseModel`은 named contract에 강하지만, 단순한 typed value, 컬렉션, `TypedDict`, union, nested generic structure를 검증할 때는 `TypeAdapter`가 더 가볍고 정확할 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: public API 계약이나 상태를 가진 named schema면 `BaseModel`, "이 타입 구조를 지금 검증하고 직렬화하고 싶다"면 `TypeAdapter`를 먼저 생각하는 편이 좋다.</p>
</div>

## 둘의 역할을 한 표로 정리

| 질문 | `BaseModel` | `TypeAdapter` |
| --- | --- | --- |
| named field contract가 필요한가 | 강함 | 약함 |
| 모델 메서드/설정이 필요한가 | 강함 | 없음 |
| 임의 타입 한 번 검증만 하고 싶은가 | 과할 수 있음 | 적합 |
| `TypedDict`, `list[Foo]`, `dict[str, int]`를 검증하고 싶은가 | wrapper model이 필요할 수 있음 | 바로 가능 |
| JSON schema 생성이 필요한가 | 가능 | 가능 |
| 재사용 가능한 validator/serializer 객체가 필요한가 | model class에 종속 | adapter 인스턴스로 직접 재사용 가능 |

## `BaseModel`이 맞는 경우

```py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime
```

- API request/response DTO
- settings object
- 이름 있는 도메인 경계 타입

## `TypeAdapter`가 더 맞는 경우

```py
from typing import TypedDict

from pydantic import TypeAdapter


class Row(TypedDict):
    id: int
    name: str


row_adapter = TypeAdapter(list[Row])

rows = row_adapter.validate_python(
    [{"id": "1", "name": "kim"}, {"id": 2, "name": "lee"}]
)
print(rows)
print(row_adapter.json_schema())
```

<p class="code-caption">단순히 `list[TypedDict]`를 검증하려고 별도 `BaseModel` wrapper를 만드는 것보다 `TypeAdapter`가 더 직관적이다. 특히 message ingestion, settings fragment, 내부 헬퍼 함수에서 유용하다.</p>

## `TypeAdapter`를 쓰면 좋은 실전 상황

- Kafka/Queue 메시지 payload 한 덩어리 검증
- ORM query 결과 projection 후 typed structure 검증
- 한 endpoint 안에서 부분 구조만 빠르게 검증
- `Annotated` 제약이 걸린 primitive나 collection 재사용

## 선택 기준 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>이름 있는 공개 계약인가</h3>
    <p>문서화와 재사용이 중요한 공개 계약이면 `BaseModel`이 자연스럽다.</p>
  </div>
  <div class="check-card">
    <h3>순수 validation utility인가</h3>
    <p>모델 클래스보다 타입 구조를 바로 검증하는 일이 핵심이면 `TypeAdapter`가 더 낫다.</p>
  </div>
  <div class="check-card">
    <h3>중첩 타입 구조가 많은가</h3>
    <p>`list[TypedDict]`, `dict[str, list[Foo]]`, union 같이 래퍼 모델이 오히려 읽기 어려운 경우 `TypeAdapter`가 유리하다.</p>
  </div>
  <div class="check-card">
    <h3>FastAPI boundary인가</h3>
    <p>FastAPI request/response schema는 보통 `BaseModel`이 더 잘 맞는다. 내부 helper와 ingestion path는 `TypeAdapter`도 적극 고려할 수 있다.</p>
  </div>
</div>

## 공식 자료

- [Type Adapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
- [Models](https://docs.pydantic.dev/latest/concepts/models/)
