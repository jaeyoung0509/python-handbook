# Metaclasses

<p class="lead">metaclass는 Python에서 가장 자주 과장되지만, 클래스가 "언제" 그리고 "어떻게" 생성되는지를 이해하려면 꼭 필요한 개념이다. 다만 중요한 건 metaclass 자체보다, metaclass가 개입하기 전후의 훨씬 더 단순한 훅들을 구분하는 것이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: metaclass는 "클래스를 만드는 클래스"지만, 대부분의 경우 `__init_subclass__`, class decorator, descriptor로 먼저 해결할 수 있다. 정말 class creation policy를 바꿔야 할 때만 metaclass를 쓴다.</p>
</div>

## 먼저 볼 그림

<MermaidDiagram
  caption="클래스 정의는 선언문처럼 보이지만, 실제로는 class body를 실행하고 그 결과 namespace로 class object를 만드는 과정이다."
  chart="flowchart LR; A[&quot;Class Statement&quot;] --> B[&quot;Execute class body&quot;]; B --> C[&quot;Namespace dict&quot;]; C --> D[&quot;Metaclass __new__&quot;]; D --> E[&quot;Class object&quot;]; E --> F[&quot;__set_name__&quot;]; E --> G[&quot;__init_subclass__ on subclasses&quot;];"
/>

## 왜 중요한가

- ORM, validation library, plugin system이 왜 "클래스 선언만 했는데 등록이 된다"처럼 보이는지 이해할 수 있다.
- class decorator, descriptor, `__init_subclass__`, metaclass 중 어디서 책임을 두는 게 맞는지 판단할 수 있다.
- framework 내부를 읽을 때 "마법"이 아니라 class creation hook 조합으로 보이기 시작한다.

## 결정 기준부터 먼저

| 도구 | 보통 쓰는 이유 | metaclass보다 먼저 고려? |
| --- | --- | --- |
| class decorator | 클래스를 후처리하고 싶을 때 | 예 |
| `__init_subclass__` | subclass 등록, 정책 강제 | 예 |
| descriptor | 필드 접근/바인딩 규칙 | 예 |
| metaclass | class object 생성 규칙 자체를 바꿀 때 | 마지막 카드 |

## 예제로 보는 "등록" 패턴

```py
class PluginRegistry(type):
    registry: dict[str, type] = {}

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> type:
        cls = super().__new__(mcls, name, bases, namespace)
        plugin_name = namespace.get("plugin_name")
        if isinstance(plugin_name, str):
            mcls.registry[plugin_name] = cls
        return cls


class PluginBase(metaclass=PluginRegistry):
    plugin_name: str


class JsonPlugin(PluginBase):
    plugin_name = "json"


class CsvPlugin(PluginBase):
    plugin_name = "csv"


print(PluginRegistry.registry)
```

<p class="code-caption">이 패턴은 declarative registration에 유용하다. 다만 subclass 등록만 필요하면 `PluginBase.__init_subclass__()`로도 충분한 경우가 많다.</p>

## 언제 metaclass를 쓰고, 언제 피하나

<div class="doc-checklist">
  <div class="check-card">
    <h3>써도 되는 경우</h3>
    <p>class body 결과를 class object 생성 시점에 강하게 통제해야 할 때, 혹은 framework DSL이 class declaration 자체를 소비할 때.</p>
  </div>
  <div class="check-card">
    <h3>피하는 경우</h3>
    <p>단순 등록, 검증, 속성 후처리 수준이면 `__init_subclass__`, decorator, descriptor로 충분한 경우가 대부분이다.</p>
  </div>
  <div class="check-card">
    <h3>주의점</h3>
    <p>metaclass는 상속 구조와 결합되기 때문에, 라이브러리 사용자에게 충돌과 학습 비용을 같이 가져온다.</p>
  </div>
</div>

## 먼저 읽어야 하는 것

- [Data Model](/pythonic/data-model)
- [Descriptors and Properties](/pythonic/descriptors-and-properties)
