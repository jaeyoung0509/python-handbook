# Object Model

<p class="lead">CPython treats almost every value as an object, so attribute lookup, method calls, mutability, identity, `__slots__`, and many performance tradeoffs all connect back to the object model.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a CPython object is useful to picture as "reference count + pointer to type + value fields." Type objects and slots drive attribute access, operator behavior, and method binding.</p>
</div>

## Start With the Structure

<MermaidDiagram
  caption="Objects point to their types, and type objects hold behavior rules and slots. Syntax and attribute access are resolved through that structure."
  chart="flowchart LR; A[PyObject instance] --> B[type pointer]; B --> C[type object]; C --> D[method slots]; C --> E[attribute rules]; E --> F[bound method creation];"
/>

## What a Bound Method Carries

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

<p class="code-caption">When you access a function through an instance, CPython creates a bound method object that carries both the original function and the bound instance.</p>

## When `__slots__` Helps

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

- `__slots__` can reduce per-instance memory by removing the instance dictionary.
- It also changes flexibility and some introspection behavior.
- That makes it a targeted optimization tool, not a default style.

## Why Mutability and Identity Matter Together

- immutable objects make sharing easier
- mutable objects separate identity from changing value
- cache keys, shared state, and default-argument surprises all connect here

## Practical Connections

- attribute-heavy domain models
- when to consider `__slots__`
- intuition for method dispatch cost

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Attribute access has a cost model</h3>
    <p>Readable syntax still goes through descriptors, instance dictionaries, and class lookup.</p>
  </div>
  <div class="check-card">
    <h3>Bound methods are objects too</h3>
    <p>Repeated method access has a small but real object-model cost.</p>
  </div>
  <div class="check-card">
    <h3>Use `__slots__` intentionally</h3>
    <p>It is a memory and layout optimization, not a universal best practice.</p>
  </div>
  <div class="check-card">
    <h3>Keep identity separate from value</h3>
    <p>That distinction becomes important whenever mutable state is shared or cached.</p>
  </div>
</div>

## Official Sources

- [Data Model](https://docs.python.org/3/reference/datamodel.html)
