# Descriptors and Properties

<p class="lead">Descriptors are one of the most important mechanisms in Python's object model. Bound methods, `property`, ORM fields, and many framework abstractions all depend on descriptor behavior.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a descriptor is an object that hooks attribute access. Data descriptors outrank instance dictionaries, while non-data descriptors do not. That single ordering rule explains a surprising amount of framework behavior.</p>
</div>

## Attribute Lookup Order First

<MermaidDiagram
  caption="Attribute lookup is not a simple dict lookup. Descriptor priority changes the result."
  chart="flowchart LR; A[obj.attr] --> B[data descriptor on class?]; B -->|yes| C[descriptor __get__]; B -->|no| D[instance __dict__]; D -->|found| E[value]; D -->|missing| F[non-data descriptor or class var]; F --> G[__getattr__ fallback];"
/>

## `property` Is Already a Descriptor

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

<p class="code-caption">`property` is not mere syntax sugar. It creates a descriptor object stored on the class, and that object controls attribute access.</p>

## A Small Custom Descriptor

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

<p class="code-caption">Framework field declarations often work like this: a descriptor instance is stored on the class and then participates in reads and writes through `__get__`, `__set__`, and `__set_name__`.</p>

## Data vs Non-Data Descriptors

- data descriptor: defines `__set__` or `__delete__`
- non-data descriptor: usually defines only `__get__`
- data descriptor beats the instance dictionary
- non-data descriptor yields to the instance dictionary

## Practical Connections

- SQLAlchemy instrumented attributes
- Pydantic field behavior and metadata access
- custom computed or validated attributes

## Read Next

- [Decorators](/en/pythonic/decorators)
- [Metaclasses](/en/pythonic/metaclasses)

## Official Sources

- [Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html)
- [Data Model](https://docs.python.org/3/reference/datamodel.html)
