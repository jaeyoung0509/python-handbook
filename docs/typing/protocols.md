# Protocols

<p class="lead">protocol은 Python의 duck typing 감각을 정적 타입 세계에 가져오는 핵심 장치다. "이 객체가 어떤 클래스의 자식인가"보다 "이 객체가 어떤 연산을 지원하는가"를 타입으로 표현할 수 있게 해준다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: `Protocol`은 상속이 아니라 capability를 기준으로 인터페이스를 표현한다. test double, plugin point, callback signature 설계에 특히 강하다.</p>
</div>

## nominal typing과 structural typing 비교

<MermaidDiagram
  caption="ABC는 주로 명시적 상속을 요구하지만, Protocol은 필요한 메서드와 속성만 맞으면 호환성을 표현할 수 있다."
  chart="flowchart LR; A[object with required methods] --> B[Protocol satisfied structurally]; C[explicit subclassing] --> D[ABC satisfied nominally];"
/>

## 가장 흔한 Protocol 예제

```py
from typing import Protocol


class SupportsWrite(Protocol):
    def write(self, data: str) -> int: ...


def write_hello(target: SupportsWrite) -> int:
    return target.write("hello")
```

## `runtime_checkable`은 제한적으로만 생각해야 한다

```py
from typing import Protocol, runtime_checkable


@runtime_checkable
class Named(Protocol):
    name: str


class User:
    name = "jae"


print(isinstance(User(), Named))
```

<p class="code-caption">`runtime_checkable`은 런타임 `isinstance()`와 연결해주지만, 정적 타입 검사만큼 정교한 모든 조건을 런타임에 완벽히 재현하는 장치는 아니다. 보조 도구로 보는 편이 안전하다.</p>

## callback protocol이 왜 중요한가

- 단순 `Callable[[...], R]`보다 의도를 더 풍부하게 표현할 수 있다.
- keyword-only, overload-like shape, stateful callback contract를 설명하기 좋다.
- event hook, framework extension point, strategy object 설계에 유용하다.

## ABC와 protocol 차이

- ABC: 명시적 상속과 런타임 계층이 중요할 때
- Protocol: 구조적 호환성과 느슨한 결합이 중요할 때
- 둘은 경쟁 관계라기보다 쓰임이 다른 도구다

## 실전 연결

- test double 설계
- pluggable interface
- framework extension point

## 공식 자료

- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [PEP 544: Protocols](https://peps.python.org/pep-0544/)
