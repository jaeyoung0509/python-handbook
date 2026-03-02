# Protocols

<p class="lead">Protocols bring Python's duck-typing intuition into the static type world. They let you describe what an object can do rather than which base class it inherits from.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: `Protocol` expresses interfaces structurally, by capability. It is especially valuable for test doubles, plugin points, and callback contracts.</p>
</div>

## Structural vs Nominal Typing

<MermaidDiagram
  caption="ABCs usually depend on explicit inheritance. Protocols depend on matching the required shape."
  chart="flowchart LR; A[object with required methods] --> B[Protocol satisfied structurally]; C[explicit subclassing] --> D[ABC satisfied nominally];"
/>

## Basic Protocol Example

```py
from typing import Protocol


class SupportsWrite(Protocol):
    def write(self, data: str) -> int: ...


def write_hello(target: SupportsWrite) -> int:
    return target.write("hello")
```

## `runtime_checkable` Is a Helper, Not a Full Static Mirror

```py
from typing import Protocol, runtime_checkable


@runtime_checkable
class Named(Protocol):
    name: str


class User:
    name = "jae"


print(isinstance(User(), Named))
```

<p class="code-caption">`runtime_checkable` lets `isinstance()` participate, but it is not a perfect runtime replay of full static protocol analysis.</p>

## Why Callback Protocols Matter

- They can express richer callback contracts than a plain `Callable`.
- They help document extension points and event hooks.
- They fit strategy objects and framework integration points well.

## ABC vs Protocol

- ABCs fit explicit runtime hierarchies.
- Protocols fit loose structural compatibility.
- They solve different design problems rather than competing directly.

## Practical Connections

- test doubles
- pluggable interfaces
- framework extension points

## Official Sources

- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [PEP 544: Protocols](https://peps.python.org/pep-0544/)
