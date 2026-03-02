# Runtime vs Static

<p class="lead">Python typing은 정적 타입 체커용 정보이면서 동시에 일부 프레임워크의 런타임 metadata이기도 하다. 이 둘을 구분하지 못하면 `Annotated`, deferred annotations, Pydantic, FastAPI가 모두 같은 타입 시스템처럼 보이면서 혼란이 커진다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 타입 체커는 annotation을 "정적 의미"로 읽고, 런타임은 annotation을 "객체 또는 표현식 metadata"로 읽는다. `Annotated`와 `annotationlib`는 이 둘의 경계를 이해할 때 특히 중요하다.</p>
</div>

## 두 세계를 나눠서 보기

<MermaidDiagram
  caption="같은 annotation이라도 type checker와 runtime/framework는 다른 목적과 해석 방식을 가진다."
  chart="flowchart LR; A[Python annotation] --> B[static type checker]; A --> C[runtime annotation reader]; B --> D[type compatibility and narrowing]; C --> E[framework metadata, dependency wiring, validation schema];"
/>

## 가장 짧은 예제

```py
from typing import Annotated

import annotationlib


def endpoint(
    user_id: Annotated[int, "path parameter"],
) -> Annotated[str, "response body"]:
    return str(user_id)


print(
    annotationlib.get_annotations(
        endpoint,
        format=annotationlib.Format.STRING,
    )
)
print(endpoint.__annotations__)
```

<p class="code-caption">정적 타입 체커는 주로 `int`, `str` 같은 타입 의미를 중심으로 보고, 런타임 도구는 `Annotated`에 담긴 metadata나 지연 평가된 annotation 표현을 같이 소비할 수 있다.</p>

## FastAPI와 Pydantic은 무엇을 소비하나

- FastAPI는 parameter annotation과 `Annotated` metadata를 읽어 request parsing과 OpenAPI schema를 구성한다.
- Pydantic은 annotation을 읽어 core schema를 만들고 validation/serialization 엔진으로 넘긴다.
- 즉, typing annotation은 더 이상 정적 분석 전용 주석이 아니다.

## 핵심 질문

- 타입 체커가 아는 것과 런타임이 아는 것은 왜 다른가?
- 어떤 annotation은 "타입"이고 어떤 annotation은 "metadata"인가?

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>정적 의미와 런타임 의미를 구분한다</h3>
    <p>타입 체커는 실행하지 않고 추론한다. 프레임워크는 실행 중 annotation 객체를 직접 읽는다.</p>
  </div>
  <div class="check-card">
    <h3>`Annotated`를 경계 도구로 쓴다</h3>
    <p>타입과 metadata를 한 자리에 두되, metadata가 타입 의미 자체와 섞이지 않게 한다.</p>
  </div>
  <div class="check-card">
    <h3>어노테이션 읽기 비용을 의식한다</h3>
    <p>deferred annotations와 `annotationlib`는 forward reference와 import cycle 부담을 줄이기 위한 장치다.</p>
  </div>
  <div class="check-card">
    <h3>framework 소비 방식을 안다</h3>
    <p>FastAPI, Pydantic, ORM이 annotation을 runtime metadata로 읽는다는 점을 알면 설계 기준이 더 선명해진다.</p>
  </div>
</div>

## 공식 자료

- [annotationlib](https://docs.python.org/3/library/annotationlib.html)
- [typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated)
