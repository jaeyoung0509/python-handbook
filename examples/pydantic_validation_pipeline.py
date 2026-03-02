# Modern Pydantic v2: core schema, validators, serializers, and TypeAdapter.
# 현대 Pydantic v2: core schema, validator, serializer, TypeAdapter.
# Why: BaseModel alone is not the full picture; the real engine is pydantic-core.
# 왜: BaseModel만으로는 부족하고, 실제 핵심 엔진은 pydantic-core다.
# Use when: designing request/response DTOs, strict parsing boundaries, or lightweight typed adapters.
# 언제 쓰나: request/response DTO, strict parsing 경계, 가벼운 typed adapter 설계에 좋다.

from __future__ import annotations

from datetime import date
from typing import Annotated, TypedDict

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    TypeAdapter,
    ValidationError,
    field_serializer,
    field_validator,
)


def positive(value: int) -> int:
    if value <= 0:
        raise ValueError("positive only")
    return value


PositiveInt = Annotated[int, AfterValidator(positive)]


class Invoice(BaseModel):
    model_config = ConfigDict(strict=False)

    invoice_id: PositiveInt
    ship_date: date
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


class Row(TypedDict):
    id: int
    name: str


def main() -> None:
    adapter = TypeAdapter(list[PositiveInt])
    print("adapter core schema type:", adapter.core_schema["type"])
    print("validated positive list:", adapter.validate_python(["1", 2, 3]))

    invoice = Invoice.model_validate(
        {
            "invoice_id": "7",
            "ship_date": "2026-03-02",
            "cents": "2500",
            "currency": "krw",
        }
    )
    print("invoice model:", invoice)
    print("invoice dump:", invoice.model_dump())
    print("invoice json-mode dump:", invoice.model_dump(mode="json"))

    row_adapter = TypeAdapter(list[Row])
    print(
        "typed rows:",
        row_adapter.validate_python(
            [
                {"id": "1", "name": "kim"},
                {"id": 2, "name": "lee"},
            ]
        ),
    )

    date_adapter = TypeAdapter(date)
    try:
        # Strict python-mode validation rejects a raw Python string for a date.
        # strict python-mode 검증은 date에 대한 raw Python 문자열을 거부한다.
        date_adapter.validate_python("2026-03-02", strict=True)
    except ValidationError as exc:
        print("strict python input error:", exc.errors()[0]["type"])

    # Strict JSON-mode validation can still accept a JSON string for a date.
    # strict JSON-mode 검증은 date에 대해 JSON 문자열을 받아들일 수 있다.
    print(
        "strict json input:",
        date_adapter.validate_json('"2026-03-02"', strict=True),
    )


if __name__ == "__main__":
    main()
