# Validation Pipeline

<p class="lead">Pydantic is not just a type check. Inputs can arrive as Python objects, JSON strings, or string-heavy configuration sources, and those inputs pass through coercion, strict checks, validators, and serializers before they become model instances or output payloads.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: the useful pipeline is `input -> coercion/strict check -> validators -> model or typed value -> serializers -> output`. Keep input rules and output rules separate if you want durable DTOs.</p>
</div>

## Pipeline Picture

<MermaidDiagram
  caption="Validation and serialization share one engine, but they should still be designed as different responsibilities."
  chart="flowchart LR; A[Python input or JSON] --> B[Coercion or strict check]; B --> C[Field and model validators]; C --> D[Typed value or BaseModel]; D --> E[field and model serializers]; E --> F[dict, JSON-ready output, error payloads];"
/>

## Inputs Come in Different Modes

- `model_validate()` / `validate_python()` for existing Python objects
- `model_validate_json()` / `validate_json()` for raw JSON
- settings and ingestion paths that are often string-heavy

## Strict Mode vs Lax Mode

Pydantic often defaults to accepting inputs that can be reasonably parsed. That is useful, but it is a real design choice.

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

<p class="code-caption">Strict JSON behavior can differ from strict Python-input behavior. The date example above is a useful reminder that transport format matters to validation policy.</p>

## Validators and Serializers Do Different Jobs

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

<p class="code-caption">Use validators to normalize and enforce input rules. Use serializers to shape output contracts. They can attach to the same field, but they should not carry the same responsibilities.</p>

## Read `ValidationError` as Structured Data

- `ValidationError.errors()` gives structured error entries.
- FastAPI builds request-validation responses from that structure.
- Error location, type, and input value are often more useful than the message text alone.

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Set strictness per boundary</h3>
    <p>Public APIs, internal event ingestion, and environment parsing often deserve different coercion policies.</p>
  </div>
  <div class="check-card">
    <h3>Keep validators focused</h3>
    <p>Validators should normalize and validate, not perform external I/O or orchestrate domain workflows.</p>
  </div>
  <div class="check-card">
    <h3>Use serializers for output contracts</h3>
    <p>Output shape belongs in serializers or DTO layers, not in ad hoc response assembly everywhere.</p>
  </div>
  <div class="check-card">
    <h3>Read errors structurally</h3>
    <p>Use `loc`, `type`, and `input` when you build good error handling or debugging workflows.</p>
  </div>
</div>

## Official Sources

- [Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
