# Internals

<p class="lead">이 장은 "Pydantic이 내부에서 무엇을 캐시하고, 무엇을 다시 빌드하고, 왜 어떤 확장은 쉽고 어떤 확장은 비용이 큰가"를 이해하기 위한 페이지다. 라이브러리 제작자 수준까지는 아니더라도, 내부 모델을 알아두면 forward reference 문제나 schema rebuild, 성능 감각이 훨씬 좋아진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Pydantic model class는 정의 시점에 field 정보와 annotation을 모으고, 그로부터 core schema를 만든 뒤 `SchemaValidator`와 `SchemaSerializer`를 준비한다. forward reference나 동적 모델 구성처럼 schema가 불완전할 수 있는 경우에만 `model_rebuild()` 같은 재구성이 필요하다.</p>
</div>

## 내부 흐름

<MermaidDiagram
  caption="모델 클래스는 선언 즉시 field metadata를 모으고, core schema를 생성한 뒤, validator/serializer 객체를 준비한다."
  chart="flowchart LR; A[Class body and annotations] --> B[model_fields build]; B --> C[Annotation resolution and config merge]; C --> D[Core schema generation]; D --> E[SchemaValidator]; D --> F[SchemaSerializer]; E --> G[model_validate path]; F --> H[model_dump path];"
/>

## 내부에서 실제로 보이는 것

```py
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


print(User.model_fields)
print(type(User.__pydantic_validator__).__name__)
print(type(User.__pydantic_serializer__).__name__)
```

<p class="code-caption">모델 클래스에는 이미 `model_fields`, `__pydantic_validator__`, `__pydantic_serializer__` 같은 내부 준비물이 붙어 있다. 즉, 매번 validation 로직을 처음부터 해석하는 구조가 아니라, 미리 준비된 객체를 재사용하는 구조다.</p>

## annotation resolution이 중요한 이유

- forward reference가 있으면 annotation을 나중에 다시 해석해야 할 수 있다.
- generic model이나 재귀 타입은 schema 생성 순서가 특히 중요하다.
- FastAPI 같은 프레임워크도 annotation을 읽고 Pydantic schema를 만들기 때문에, runtime annotation 해석 방식과 바로 연결된다.

## `model_rebuild()`는 언제 나오나

- forward reference가 아직 풀리지 않았을 때
- 동적으로 model class를 조합하거나 generic parameter를 확정할 때
- import cycle이나 지연된 타입 정의로 인해 초기 schema가 완전하지 않을 때

## caching과 reuse의 감각

- model class마다 validator/serializer가 준비된다.
- `TypeAdapter`도 adapter 인스턴스 단위로 validator/serializer를 재사용한다.
- 그래서 hot path에서는 adapter/model 객체를 재생성하지 않고 재사용하는 편이 좋다.

## framework 관점에서 중요한 경계

<div class="doc-checklist">
  <div class="check-card">
    <h3>annotation reading</h3>
    <p>framework는 Python annotation을 직접 소비하는 것이 아니라, 종종 Pydantic schema generation 단계로 넘긴다.</p>
  </div>
  <div class="check-card">
    <h3>schema cache</h3>
    <p>같은 model/adapter를 재사용할수록 validator/serializer 준비 비용을 다시 내지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>dynamic model cost</h3>
    <p>동적 모델 생성과 rebuild는 유연하지만, 정적 선언보다 이해와 디버깅 비용이 높다.</p>
  </div>
  <div class="check-card">
    <h3>custom hooks</h3>
    <p>아주 깊은 확장은 core schema hook 수준으로 내려가지만, 그만큼 Pydantic 내부 모델을 더 정확히 이해해야 한다.</p>
  </div>
</div>

## 공식 자료

- [Pydantic Architecture](https://docs.pydantic.dev/latest/internals/architecture/)
- [Resolving Annotations](https://docs.pydantic.dev/latest/internals/resolving_annotations/)
