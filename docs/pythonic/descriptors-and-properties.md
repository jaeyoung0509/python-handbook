# Descriptors and Properties

<p class="lead">descriptor는 Python framework를 이해하는 가장 중요한 장치 중 하나다. 함수의 method binding, `property`, ORM field, computed attribute가 모두 descriptor 규약 위에서 돌아간다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: descriptor는 "attribute access에 개입하는 객체"다. data descriptor는 instance dict보다 우선하고, non-data descriptor는 그보다 늦게 본다. 이 우선순위가 `property`, method binding, framework field 동작을 결정한다.</p>
</div>

## attribute lookup 순서를 먼저 잡기

<MermaidDiagram
  caption="instance attribute access는 단순 dict lookup이 아니다. descriptor 종류에 따라 우선순위가 다르다."
  chart="flowchart LR; A[&quot;obj.attr&quot;] --> B[&quot;data descriptor on class?&quot;]; B -->|yes| C[&quot;descriptor __get__&quot;]; B -->|no| D[&quot;instance __dict__&quot;]; D -->|found| E[&quot;value&quot;]; D -->|missing| F[&quot;non-data descriptor or class var&quot;]; F --> G[&quot;__getattr__ fallback&quot;];"
/>

## `property`도 사실 descriptor다

```py
class Celsius:
    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, number: float) -> None:
        if number < -273.15:
            raise ValueError("below absolute zero")
        self._value = number


temp = Celsius(20.0)
print(temp.value)
temp.value = 25.0
```

<p class="code-caption">`property`는 getter/setter를 감싼 descriptor 객체다. 단순 문법 설탕이 아니라, class attribute에 저장된 특별한 객체가 attribute access를 가로채는 구조다.</p>

## 직접 descriptor를 만들면 왜 유용한가

```py
class PositiveNumber:
    def __set_name__(self, owner: type, name: str) -> None:
        self.private_name = f"_{name}"

    def __get__(self, instance: object | None, owner: type | None = None) -> object:
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance: object, value: int) -> None:
        if value <= 0:
            raise ValueError("positive only")
        setattr(instance, self.private_name, value)


class Product:
    stock = PositiveNumber()

    def __init__(self, stock: int) -> None:
        self.stock = stock


product = Product(10)
print(product.stock)
```

<p class="code-caption">framework field가 종종 이렇게 동작한다. class body에 descriptor 인스턴스를 두고, `__set_name__`, `__get__`, `__set__`로 access 규칙을 정의한다.</p>

## data descriptor vs non-data descriptor

- data descriptor: `__set__` 또는 `__delete__`가 있음
- non-data descriptor: 보통 `__get__`만 있음
- data descriptor는 instance dict보다 우선
- non-data descriptor는 instance dict 뒤에서 본다

## 실전 연결

- SQLAlchemy instrumented attribute
- Pydantic field metadata 접근
- custom validation/computed attribute 설계

## 이어서 읽기

- [Decorators](/pythonic/decorators)
- [Metaclasses](/pythonic/metaclasses)

## 공식 자료

- [Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html)
- [Data Model](https://docs.python.org/3/reference/datamodel.html)
