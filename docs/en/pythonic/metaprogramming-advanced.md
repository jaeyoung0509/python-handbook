# Metaprogramming Advanced

<p class="lead">Metaprogramming is not just a bag of tricks. It is a design tool for reducing repetition and exposing declarative APIs. The key is cost-aware tool selection: choose the smallest hook that solves the problem cleanly.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: if two hooks can solve the same problem, pick the simpler one. In practice, the ladder is descriptor / `__set_name__` -> `__init_subclass__` -> class decorator -> metaclass -> import hook. The success criterion is not "more magic"; it is lower maintenance cost with clearer intent.</p>
</div>

## Hook Selection Ladder

<MermaidDiagram
  caption="Power increases upward, but so does maintenance and debugging cost."
  chart="flowchart TB; A[&quot;Descriptor / __set_name__&quot;] --> B[&quot;__init_subclass__&quot;]; B --> C[&quot;Class decorator&quot;]; C --> D[&quot;Metaclass&quot;]; D --> E[&quot;Import hook&quot;];"
/>

## 1) `__set_name__`: when field-name binding matters

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

Use it for:

- field-level access policy
- validation/caching/lazy binding
- descriptor behavior that depends on class attribute names

## 2) `__init_subclass__`: enforce or register subclass contracts

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

Use it for:

- plugin registration
- subclass validation
- class-level policy without full metaclass cost

## 3) Class decorators: preserve declaration ergonomics, apply post-processing

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

Use it for:

- post-processing class objects
- registration plus metadata injection
- combining with dataclass/attrs/pydantic style decorators

## 4) Metaclasses: only when class creation policy must be controlled

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

Use it for:

- class-body DSL interpretation
- hard class-creation policy
- cases where decorators and `__init_subclass__` are insufficient

## 5) Import hooks and AST transforms: only for strong global needs

- highest cost, highest surprise potential
- impacts debugging and tooling significantly
- avoid unless there is a team-wide policy reason

## Common Open-source Shapes

- Click/FastAPI: declarative decorators delegating to core registration functions
- SQLAlchemy: descriptor plus class-construction hook composition
- Pydantic: thin public methods delegating to internal validator engines

See [Open-source Pythonic Deep Dives](/en/pythonic/opensource-pythonic-patterns) for concrete code excerpts.

## Review Checklist

- Could a lower-cost hook solve this?
- Is runtime behavior explicit at boundaries (inputs, outputs, errors)?
- Can a new team member read and modify this safely?
- Is test substitution (fakes/mocks) straightforward?
- Is the hook choice documented with rationale?

## Runnable Labs in This Repository

- `examples/metaprogramming_hooks_lab.py`
- `examples/usecase_with_uow_abc.py`

## Official References

- [Data Model](https://docs.python.org/3/reference/datamodel.html)
- [Descriptor HowTo Guide](https://docs.python.org/3/howto/descriptor.html)
- [importlib](https://docs.python.org/3/library/importlib.html)
- [ast](https://docs.python.org/3/library/ast.html)
