# Typing Review Checklist

<p class="lead">팀에서 typing을 쓴다고 해서 타입 품질이 자동으로 좋아지지는 않는다. 오히려 `Any`가 숨어 있고, alias가 의미 없이 늘어나고, validation 책임과 타입 책임이 섞이면 "타입이 있으니 안전하다"는 착시만 커질 수 있다. 이 문서는 코드 리뷰에서 실제로 봐야 할 질문을 정리한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 좋은 타입 리뷰는 문법 채우기 검사가 아니라 boundary 설계 검사다. 공개 API 시그니처가 설명적인지, `Any`가 바깥으로 새는지, protocol과 concrete type이 적절히 분리되는지, validation과 typing을 혼동하지 않는지가 핵심이다.</p>
</div>

## 타입 리뷰 흐름

<MermaidDiagram
  caption="타입 리뷰는 '애노테이션이 있나'보다 '경계가 설명되나'를 먼저 본다."
  chart="flowchart LR; A[Public function or class] --> B{Is the boundary explicit?}; B -->|No| C[Fix signature and DTOs]; B -->|Yes| D{Does Any leak?}; D -->|Yes| E[Constrain boundary types]; D -->|No| F{Protocol or concrete type chosen well?}; F -->|No| G[Refine abstraction]; F -->|Yes| H[Check validation and runtime assumptions];"
/>

## 1. 공개 시그니처가 설명적인가

- 함수 인자와 반환 타입이 호출자 관점에서 충분히 설명적인가
- `dict[str, Any]` 대신 `TypedDict`, DTO, protocol 같은 더 구체적인 타입이 가능한가
- public API가 내부 구현 타입에 과도하게 묶여 있지 않은가

## 2. `Any`가 boundary 밖으로 새는가

```py
from typing import Any


def parse_payload(raw: dict[str, Any]) -> CreateUserCommand:
    ...
```

입력 직후 boundary에서는 `Any`가 잠깐 있을 수 있다. 문제는 이 값이 service, repository, domain 레이어까지 그대로 퍼지는 경우다. `Any`는 경계에서 좁히고, 안쪽으로 들어갈수록 더 구체적인 타입으로 바꿔야 한다.

## 3. alias가 의미를 만들고 있는가

### 좋은 alias

- 도메인 의미를 추가한다
- 반복되는 구조를 줄인다
- API 문서성과 재사용성을 높인다

### 나쁜 alias

- 단지 길이를 줄이기 위해 `type Data = dict[str, object]`를 만든다
- 한 번만 쓰는 사소한 타입을 별칭으로 뽑아 가독성을 오히려 해친다

## 4. protocol과 concrete type을 구분했는가

- 확장 지점이면 protocol이 적합할 수 있다.
- 내부 구현이 확정된 레이어면 concrete type이 더 읽기 쉬울 수 있다.
- DI를 한다고 모든 것을 protocol로 추상화하면 오히려 인터페이스가 공허해진다.

## 5. validation과 typing 책임을 섞지 않았는가

- typing은 "호출자와 구현자 사이 계약"에 가깝다.
- validation은 "신뢰할 수 없는 입력을 어떻게 정제할 것인가"에 가깝다.
- `str` 타입이 붙어 있다고 해서 외부 JSON 입력이 자동으로 안전해지는 것은 아니다.
- FastAPI/Pydantic boundary에서 validation 후 더 구체적 타입으로 넘기는 구조가 좋다.

## 리뷰어가 바로 볼 수 있는 냄새

| 냄새 | 왜 문제인가 | 보통의 수정 방향 |
| --- | --- | --- |
| `Any`가 서비스 전체에 퍼짐 | 타입 체커가 거의 무력화됨 | boundary에서 DTO/TypedDict로 좁힘 |
| `cast()`가 자주 등장 | 타입 모델과 실제 데이터 흐름이 어긋남 | predicate, `TypeGuard`, validation 경계 도입 |
| protocol이 지나치게 많음 | 구현보다 추상화가 앞서감 | 진짜 확장 지점만 protocol 유지 |
| request/response/ORM 타입이 하나로 합쳐짐 | 책임이 섞여 진화가 어려움 | DTO와 entity 분리 |
| alias가 너무 많음 | 타입 읽기가 오히려 느려짐 | 의미 있는 alias만 남김 |

## 코드 리뷰 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>Boundary first</h3>
    <p>이 함수나 클래스가 외부와 맺는 계약이 무엇인지 애노테이션만 보고도 읽히는가.</p>
  </div>
  <div class="check-card">
    <h3>`Any` containment</h3>
    <p>불가피한 `Any`가 있더라도 boundary 근처에서 좁혀지고, 안쪽 레이어로 퍼지지 않는가.</p>
  </div>
  <div class="check-card">
    <h3>Abstraction discipline</h3>
    <p>protocol, generic, alias가 실제 유연성을 만드는지, 아니면 장식인지 구분했는가.</p>
  </div>
  <div class="check-card">
    <h3>Runtime reality</h3>
    <p>typing만 믿고 런타임 validation이나 serialization 경계를 잊고 있지 않은가.</p>
  </div>
</div>

## 함께 보면 좋은 예제

- `examples/py310_typing_and_zip_strict.py`
- `examples/py312_type_params.py`
- `examples/pydantic_validation_pipeline.py`

## 공식 자료

- [Python typing](https://docs.python.org/3/library/typing.html)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [Pydantic Type Adapter](https://docs.pydantic.dev/latest/concepts/type_adapter/)
