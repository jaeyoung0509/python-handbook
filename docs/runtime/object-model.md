# Object Model

<p class="lead">CPython은 거의 모든 값을 객체로 다룬다. 따라서 attribute lookup, method call, mutability, identity, `__slots__`, 작은 객체의 생성/삭제 비용 같은 것들은 전부 object model과 연결된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: CPython 객체는 대체로 "참조 카운트 + type pointer + 값/필드"라는 감각으로 보면 된다. 어떤 연산이 가능한지, attribute access가 어떻게 해석되는지, method가 왜 bind되는지가 모두 type object와 slot에서 나온다.</p>
</div>

## object model을 한 그림으로 보기

<MermaidDiagram
  caption="객체는 자기 type을 가리키고, type object는 연산 규칙과 slot을 가진다. 문법과 attribute access는 결국 이 구조 위에서 동작한다."
  chart="flowchart LR; A[PyObject instance] --> B[type pointer]; B --> C[type object]; C --> D[method slots]; C --> E[attribute rules]; E --> F[bound method creation];"
/>

## bound method가 실제로 뭘 담는지 보기

```py
class User:
    def greet(self) -> str:
        return "hello"


user = User()
method = user.greet

print("bound method type:", type(method).__name__)
print("method.__self__ is user:", method.__self__ is user)
print("method.__func__ is User.greet:", method.__func__ is User.greet)
```

<p class="code-caption">instance에서 함수를 읽으면 bound method 객체가 생기고, 거기에는 원래 함수와 바인딩된 instance가 함께 들어 있다. 이 때문에 method call은 단순 함수 호출과는 다른 비용 구조를 가진다.</p>

## `__slots__`는 언제 의미가 있나

```py
class RegularUser:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age


class SlottedUser:
    __slots__ = ("name", "age")

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age
```

- `__slots__`는 instance `__dict__`를 없애 메모리와 lookup 경로를 줄일 수 있다.
- 대신 유연성을 희생한다.
- 따라서 대규모 instance 수, 아주 단순한 데이터 object, memory pressure가 있을 때 고려하는 편이 좋다.

## mutability와 identity를 같이 봐야 하는 이유

- immutable object는 같은 값을 공유하기 쉬운 반면
- mutable object는 identity와 value 변화가 함께 설계 문제를 만든다
- cache key, shared state, default argument bug 같은 주제가 여기와 연결된다

## 실전 연결

- attribute-heavy domain model
- `__slots__`를 언제 고려할지
- method dispatch cost 감각

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>attribute access 비용</h3>
    <p>Python의 읽기 쉬운 문법 뒤에는 descriptor, instance dict, class lookup이 들어간다. hot path면 비용 감각이 필요하다.</p>
  </div>
  <div class="check-card">
    <h3>bound method 생성</h3>
    <p>instance method access는 binding object를 만든다. 반복 access가 많은 코드에서는 미세하지만 누적 비용이 있을 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>`__slots__` 남용 주의</h3>
    <p>메모리 최적화 카드이지 기본값은 아니다. introspection, 확장성, 라이브러리 호환성 비용도 같이 본다.</p>
  </div>
  <div class="check-card">
    <h3>identity와 값 구분</h3>
    <p>mutable object를 다룰 때는 "같은 객체인가"와 "같은 값인가"를 분리해서 생각해야 한다.</p>
  </div>
</div>

## 공식 자료

- [Data Model](https://docs.python.org/3/reference/datamodel.html)
