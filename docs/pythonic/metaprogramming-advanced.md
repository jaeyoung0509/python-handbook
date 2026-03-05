# 메타프로그래밍 심화

<p class="lead">메타프로그래밍은 "고급 기교"가 아니라, 중복을 줄이고 선언형 API를 만드는 설계 도구다. 다만 도구 선택을 잘못하면 팀 전체 디버깅 비용이 크게 올라간다. 이 페이지는 `__set_name__`, `__init_subclass__`, class decorator, metaclass, import hook을 "작은 도구부터" 고르는 기준으로 정리한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 같은 문제를 풀 수 있다면 항상 더 단순한 훅부터 쓴다. 보통 순서는 descriptor / `__set_name__` -> `__init_subclass__` -> class decorator -> metaclass -> import hook 이다. 메타프로그래밍의 성공 기준은 "마법처럼 보이게 하는 것"이 아니라 "의도를 짧게, 비용을 낮게" 만드는 것이다.</p>
</div>

## 훅 선택 사다리

<MermaidDiagram
  caption="위로 갈수록 강력하지만 비용이 커진다. 대부분은 아래쪽 훅으로 충분하다."
  chart="flowchart TB; A[&quot;Descriptor / __set_name__&quot;] --> B[&quot;__init_subclass__&quot;]; B --> C[&quot;Class decorator&quot;]; C --> D[&quot;Metaclass&quot;]; D --> E[&quot;Import hook&quot;];"
/>

## 1) `__set_name__`: 필드 이름 바인딩이 필요할 때

```py
class Positive:
    def __set_name__(self, owner: type, name: str) -> None:
        self.private_name = f"_{name}"

    def __get__(self, instance: object | None, owner: type | None = None) -> object:
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance: object, value: int) -> None:
        if value <= 0:
            raise ValueError("must be positive")
        setattr(instance, self.private_name, value)
```

언제 쓰나:

- field-level access rule
- validation/caching/lazy binding
- class body의 attribute 이름을 descriptor가 알아야 할 때

## 2) `__init_subclass__`: subclass 정책 강제/등록

```py
class HandlerBase:
    registry: dict[str, type["HandlerBase"]] = {}

    def __init_subclass__(cls, *, key: str | None = None, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if key is not None:
            HandlerBase.registry[key] = cls


class JsonHandler(HandlerBase, key="json"):
    pass
```

언제 쓰나:

- plugin 등록
- subclass contract 검증
- metaclass까지 갈 필요 없는 class registration

## 3) class decorator: 선언문 문맥을 살리고 후처리할 때

```py
from dataclasses import dataclass


def service(name: str):
    def decorator(cls: type) -> type:
        cls.service_name = name
        return dataclass(slots=True)(cls)

    return decorator


@service("billing")
class BillingConfig:
    retries: int = 3
```

언제 쓰나:

- class object 후처리
- 등록 + metadata 주입
- dataclass/attrs/pydantic decorator 조합

## 4) metaclass: class creation policy 자체를 바꿔야 할 때

```py
class NoMutableDefaults(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> type:
        for key, value in namespace.items():
            if isinstance(value, (list, dict, set)):
                raise TypeError(f"{name}.{key} has mutable class default")
        return super().__new__(mcls, name, bases, namespace)
```

언제 쓰나:

- class body를 DSL처럼 해석
- class 생성 시점 강제 규칙
- `__init_subclass__`나 decorator로는 어려운 정책 적용

## 5) import hook/AST 변환: 팀 규칙을 빌드/실행 경계에서 강제할 때

- cost가 가장 크다.
- 개발자 경험과 디버깅 난이도에 큰 영향이 있다.
- "팀 전체 공통 규칙" 같은 강한 이유가 없으면 피하는 편이 낫다.

## 오픈소스에서 반복되는 모양

- Click/FastAPI: decorator로 선언형 API 제공, core 함수로 위임
- SQLAlchemy: descriptor/class construction 훅 조합
- Pydantic: public API는 얇게 두고 내부 validator 엔진으로 위임

자세한 사례는 [오픈소스 Pythonic 딥다이브](/pythonic/opensource-pythonic-patterns)에서 본다.

## 코드 리뷰 체크리스트

- 이 훅보다 더 아래 단계 도구로 풀 수 없는가?
- 디버깅 시 경로가 투명한가(입력/출력/예외)?
- 팀 내 새 개발자가 읽고 수정 가능한가?
- 테스트 더블(fakes/mocks)로 대체가 쉬운가?
- 문서에 "왜 이 훅을 골랐는지"가 남아 있는가?

## 이 저장소 실험 예제

- `examples/metaprogramming_hooks_lab.py`
- `examples/usecase_with_uow_abc.py`

## 공식 자료

- [Data Model](https://docs.python.org/3/reference/datamodel.html)
- [Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html)
- [importlib](https://docs.python.org/3/library/importlib.html)
- [ast](https://docs.python.org/3/library/ast.html)
