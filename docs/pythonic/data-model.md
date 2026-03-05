# Data Model

<p class="lead">Python을 Python답게 만드는 중심축은 data model이다. 함수가 method처럼 보이는 이유, `len(obj)`가 가능한 이유, attribute lookup이 왜 framework의 마법처럼 느껴지는지 모두 여기서 나온다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Python 문법의 많은 부분은 객체의 dunder method와 연결된다. `len(obj)`, `obj[x]`, `obj.attr`, 함수의 method binding까지 모두 data model의 표현이다.</p>
</div>

## 먼저 그림으로 보기

<MermaidDiagram
  caption="문법은 결국 객체 모델과 연결된다. 연산자, attribute access, method call은 전부 type과 dunder method를 통해 해석된다."
  chart="flowchart LR; A[&quot;Python syntax&quot;] --> B[&quot;Type object&quot;]; B --> C[&quot;dunder methods and slots&quot;]; C --> D[&quot;attribute access&quot;]; C --> E[&quot;operator behavior&quot;]; C --> F[&quot;method binding&quot;];"
/>

## 왜 중요한가

- 함수가 클래스에 들어가면 왜 bound method가 되는지 이해할 수 있다.
- `__getattribute__`, `__getattr__`, descriptor가 어떤 순서로 개입하는지 설명할 수 있다.
- framework internals가 "마법"이 아니라 data model hook 조합으로 보이기 시작한다.

## identity / type / value를 분리해서 생각하기

- identity: `id(obj)`로 구분되는 "같은 객체인가"
- type: 어떤 연산과 규칙을 제공하는가
- value: 현재 그 객체가 표현하는 상태

Python은 이 세 가지를 명확히 구분하는 언어다. mutable object는 identity는 같고 value만 바뀔 수 있다.

## 함수가 method처럼 보이는 이유

```py
class User:
    def greet(self) -> str:
        return f"hello from {self.__class__.__name__}"


user = User()
print("class attribute:", User.greet)
print("instance attribute:", user.greet)
print("call result:", user.greet())
```

<p class="code-caption">클래스에 저장된 함수 객체는 instance에서 읽을 때 bound method로 바뀐다. 이 binding도 data model의 일부이고, 함수 객체가 descriptor처럼 동작하기 때문에 가능하다.</p>

## attribute lookup에서 가장 자주 헷갈리는 지점

```py
class Profile:
    def __init__(self) -> None:
        self.name = "jae"

    def __getattribute__(self, name: str) -> object:
        print("getattribute:", name)
        return super().__getattribute__(name)

    def __getattr__(self, name: str) -> str:
        return f"<missing {name}>"


profile = Profile()
print(profile.name)
print(profile.nickname)
```

<p class="code-caption">`__getattribute__`는 거의 모든 attribute access에서 먼저 호출되고, 거기서 `AttributeError`가 나야 `__getattr__`이 fallback으로 호출된다. 둘을 바꿔 생각하면 디버깅이 매우 어려워진다.</p>

## 실전에서 특히 중요한 질문

<div class="doc-checklist">
  <div class="check-card">
    <h3>왜 `len(obj)`는 `obj.len()`이 아닌가</h3>
    <p>문법이 객체 내부 메서드 이름에 직접 붙는 것이 아니라, type slot과 dunder method 규약을 통해 연결되기 때문이다.</p>
  </div>
  <div class="check-card">
    <h3>왜 함수가 method처럼 보이나</h3>
    <p>함수 객체가 class attribute로 저장될 때 descriptor처럼 binding에 참여하기 때문이다.</p>
  </div>
  <div class="check-card">
    <h3>왜 framework field가 마법처럼 동작하나</h3>
    <p>class body, descriptor, metaclass, annotation consumption이 data model 위에서 합쳐지기 때문이다.</p>
  </div>
  <div class="check-card">
    <h3>언제 `__getattribute__`를 건드리나</h3>
    <p>정말 전역적인 attribute interception이 필요할 때만 쓴다. 대부분은 descriptor나 property가 더 안전하다.</p>
  </div>
</div>

## 이어서 읽기

- [Descriptors and Properties](/pythonic/descriptors-and-properties)
- [Runtime Object Model](/runtime/object-model)

## 공식 자료

- [Data Model](https://docs.python.org/3/reference/datamodel.html)
