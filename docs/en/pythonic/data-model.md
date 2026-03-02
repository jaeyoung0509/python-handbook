# Data Model

<p class="lead">The Python data model is what makes Python feel like Python. Method binding, attribute access, operator behavior, and many framework-level tricks are all expressions of the same object protocol.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: a lot of Python syntax is just a readable front-end for object protocol methods. `len(obj)`, `obj[x]`, `obj.attr`, and bound methods all come from the data model.</p>
</div>

## See the Model First

<MermaidDiagram
  caption="Python syntax maps to object protocol behavior through type objects, slots, and dunder methods."
  chart="flowchart LR; A[Python syntax] --> B[Type object]; B --> C[dunder methods and slots]; C --> D[attribute access]; C --> E[operator behavior]; C --> F[method binding];"
/>

## Why It Matters

- It explains why functions turn into bound methods on instances.
- It makes attribute lookup and descriptors feel mechanical instead of magical.
- It gives you the right base layer for reading framework internals.

## Separate Identity, Type, and Value

- identity: whether this is the same object
- type: which behaviors and rules are attached
- value: the object's current state

Python draws a strong line between them. Mutable objects can keep the same identity while their value changes.

## Why Functions Become Methods

```py
class User:
    def greet(self) -> str:
        return f"hello from {self.__class__.__name__}"


user = User()
print("class attribute:", User.greet)
print("instance attribute:", user.greet)
print("call result:", user.greet())
```

<p class="code-caption">The function stored on the class is transformed into a bound method when accessed through an instance. That binding behavior is part of the data model.</p>

## Attribute Lookup Gets Interesting Fast

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

<p class="code-caption">`__getattribute__` runs for almost every attribute access. `__getattr__` is only a fallback after normal lookup fails.</p>

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Why not `obj.len()`?</h3>
    <p>Python syntax is attached to protocol hooks and slots, not to arbitrary instance method naming.</p>
  </div>
  <div class="check-card">
    <h3>Why do methods bind?</h3>
    <p>Functions on classes behave like descriptors and participate in binding.</p>
  </div>
  <div class="check-card">
    <h3>Why do frameworks feel magical?</h3>
    <p>Because class bodies, descriptors, metaclasses, and annotations all build on this model.</p>
  </div>
  <div class="check-card">
    <h3>When do you override `__getattribute__`?</h3>
    <p>Only when you need global interception. Descriptors and properties are usually the safer tool.</p>
  </div>
</div>

## Read Next

- [Descriptors and Properties](/en/pythonic/descriptors-and-properties)
- [Object Model](/en/runtime/object-model)

## Official Sources

- [Data Model](https://docs.python.org/3/reference/datamodel.html)
