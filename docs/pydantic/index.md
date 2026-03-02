# Pydantic

<p class="lead">이 파트는 Pydantic v2를 "예쁜 모델 선언 라이브러리"가 아니라, Python 타입 힌트를 입력으로 받아 validation과 serialization을 수행하는 엔진으로 읽는다. `BaseModel`은 입구일 뿐이고, 실제 핵심은 `pydantic-core`, core schema, `TypeAdapter`, strict/lax 동작 구분에 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Pydantic을 깊게 이해하려면 `BaseModel` 메서드 이름보다 "annotation -> core schema -> validator/serializer -> DTO" 흐름을 먼저 잡아야 한다. 그래야 FastAPI, settings, 메시지 파이프라인, 타입 설계가 한 그림으로 보인다.</p>
</div>

## 이 파트에서 잡아야 할 감각

<div class="reading-grid">
  <div class="reading-card">
    <h3>BaseModel 바깥 보기</h3>
    <p>`BaseModel`은 named contract에 강하지만, Pydantic의 진짜 범위는 훨씬 넓다. `TypeAdapter`로 임의 타입도 같은 엔진에 태울 수 있다.</p>
  </div>
  <div class="reading-card">
    <h3>Strict와 Lax 구분</h3>
    <p>Pydantic의 기본은 "파싱 가능한 입력을 받아들인다"에 가깝다. 언제 coercion을 허용하고 언제 strict하게 막을지 아는 것이 API 품질을 좌우한다.</p>
  </div>
  <div class="reading-card">
    <h3>Validation과 Serialization 분리</h3>
    <p>입력을 받아들이는 규칙과 출력을 직렬화하는 규칙은 다르다. validator와 serializer를 섞어 생각하면 schema가 금방 지저분해진다.</p>
  </div>
  <div class="reading-card">
    <h3>Framework 소비 방식 이해</h3>
    <p>FastAPI는 annotation을 보고 Pydantic으로 request/response 경계를 만든다. 그래서 typing, runtime introspection, Pydantic이 분리된 주제가 아니다.</p>
  </div>
</div>

## 추천 순서

1. [Core Schema](/pydantic/core-schema)
2. [Validation Pipeline](/pydantic/validation-pipeline)
3. [BaseModel vs TypeAdapter](/pydantic/basemodel-vs-typeadapter)
4. [Internals](/pydantic/internals)

## 이 파트의 실전 규칙

- `BaseModel`만으로 모든 것을 해결하려 하지 않는다.
- request/response DTO와 internal validation adapter를 구분한다.
- strict/lax 정책을 엔드포인트와 ingestion 경계별로 정한다.
- serializer는 출력 계약을 위해 쓰고, validator는 입력 규칙을 위해 쓴다.
