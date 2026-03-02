# Validation Pipeline

<p class="lead">Pydantic은 단순 "타입이 맞는가"만 보는 도구가 아니다. 입력은 Python object일 수도, JSON string일 수도, 환경 변수 문자열일 수도 있고, 그 입력은 coercion, strict 검사, validator, serializer를 거쳐 최종 객체나 출력 형태로 바뀐다. 이 파이프라인을 이해해야 API와 ingestion boundary를 안정적으로 설계할 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Pydantic 파이프라인은 `input -> coercion/strict check -> validators -> model or typed value -> serializers -> output` 으로 생각하는 편이 가장 정확하다. 입력 규칙과 출력 규칙을 분리해서 설계해야 DTO가 오래 버틴다.</p>
</div>

## 파이프라인 그림

<MermaidDiagram
  caption="입력 검증과 출력 직렬화는 같은 엔진 위에서 돌아가지만, 책임은 분리해서 생각하는 편이 좋다."
  chart="flowchart LR; A[Python input or JSON] --> B[Coercion or strict check]; B --> C[Field and model validators]; C --> D[Typed value or BaseModel]; D --> E[field and model serializers]; E --> F[dict, JSON-ready output, error payloads];"
/>

## 입력은 여러 모드가 있다

- `model_validate()` / `validate_python()`: 이미 Python 객체인 입력 검증
- `model_validate_json()` / `validate_json()`: JSON 문자열에서 바로 검증
- settings나 ingestion path: 문자열 기반 입력을 많이 받음

## lax 기본값과 strict 모드의 차이

Pydantic의 기본은 "합리적으로 파싱 가능한 입력을 받아들인다"에 가깝다. 그래서 `int` 필드에 `"3"`이 들어오면 기본적으로 정수 3으로 바뀔 수 있다.

```py
from datetime import date

from pydantic import TypeAdapter, ValidationError


adapter = TypeAdapter(date)

try:
    adapter.validate_python("2026-03-02", strict=True)
except ValidationError as exc:
    print("strict python input:", exc.errors()[0]["type"])

print(
    "strict json input:",
    adapter.validate_json('"2026-03-02"', strict=True),
)
```

<p class="code-caption">strict 모드에서도 JSON 입력은 Python 입력과 다르게 허용되는 경우가 있다. 날짜 같은 타입은 JSON 문자열에서 strict하게 받아들여질 수 있지만, Python 문자열에서 strict하게 받아들이지 않을 수 있다. 이 차이는 공식 strict mode 문서에서 특히 강조하는 포인트다.</p>

## validator와 serializer를 분리해서 보자

```py
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


class Invoice(BaseModel):
    model_config = ConfigDict(strict=False)

    cents: int
    currency: str

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"USD", "KRW"}:
            raise ValueError("unsupported currency")
        return normalized

    @field_serializer("cents")
    def serialize_cents(self, value: int) -> str:
        return f"{value / 100:.2f}"


invoice = Invoice.model_validate({"cents": "2500", "currency": "krw"})
print(invoice)
print(invoice.model_dump())
print(invoice.model_dump(mode="json"))
```

<p class="code-caption">`field_validator`는 입력 정규화와 검증에 쓰고, `field_serializer`는 출력 계약을 다듬는 데 쓴다. 둘 다 같은 field에 걸 수 있지만, 역할은 다르다.</p>

## ValidationError를 API 에러 모델로 읽기

- `ValidationError.errors()`는 기계가 읽기 좋은 구조화된 에러 목록이다.
- FastAPI는 이 구조를 이용해 request validation 에러를 HTTP 응답으로 바꾼다.
- 따라서 에러 메시지 문자열만 보지 말고 location, type, input 값을 같이 보는 편이 좋다.

## 실전 설계 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>입력 경계마다 strict 정책 지정</h3>
    <p>외부 공개 API, 내부 이벤트 소비, 환경 변수 파싱은 같은 strict 정책을 쓰지 않는 경우가 많다.</p>
  </div>
  <div class="check-card">
    <h3>validator는 정규화와 규칙에 집중</h3>
    <p>외부 I/O나 DB 접근까지 validator에 넣기 시작하면 테스트와 재사용성이 급격히 나빠진다.</p>
  </div>
  <div class="check-card">
    <h3>serializer는 출력 계약용</h3>
    <p>출력 표현을 위한 규칙을 serializer에 두고, 내부 저장 표현과 분리한다.</p>
  </div>
  <div class="check-card">
    <h3>에러를 구조로 본다</h3>
    <p>`ValidationError.errors()`의 `loc`, `type`, `input`은 API 에러 품질을 높이는 핵심 정보다.</p>
  </div>
</div>

## 공식 자료

- [Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)

## 실전 연결

- API boundary
- settings model
- message ingestion pipeline
