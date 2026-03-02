# Metaclasses

<p class="lead">Metaclasses are often oversold. The real skill is not "knowing metaclasses" but knowing where class decorators, descriptors, and `__init_subclass__` stop being enough.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: use a metaclass only when you need to change class creation itself. For registration, validation, or light post-processing, simpler hooks usually work better.</p>
</div>

## Start With the Creation Timeline

<MermaidDiagram
  caption="A class statement looks declarative, but Python actually executes the class body, builds a namespace, and then constructs a class object."
  chart="flowchart LR; A[Class Statement] --> B[Execute class body]; B --> C[Namespace dict]; C --> D[Metaclass __new__]; D --> E[Class object]; E --> F[__set_name__]; E --> G[__init_subclass__ on subclasses];"
/>

## Why It Matters

- Frameworks that feel "magical" usually hook into class creation.
- You need the right tool for the job: decorator, descriptor, `__init_subclass__`, or metaclass.
- Once you see the timeline, declarative ORM or validation APIs stop feeling mysterious.

## Pick the Smallest Tool

| Tool | Usual purpose | Consider before a metaclass? |
| --- | --- | --- |
| Class decorator | Post-process a class | Yes |
| `__init_subclass__` | Register or validate subclasses | Yes |
| Descriptor | Control field access and binding | Yes |
| Metaclass | Change how class objects are created | Last resort |

## Example: Declarative Registration

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

<p class="code-caption">This works well for declarative registration. But if registration is the only goal, `__init_subclass__()` is often simpler and easier for library users to compose.</p>

## When It Is Worth It

<div class="doc-checklist">
  <div class="check-card">
    <h3>Good fit</h3>
    <p>You need to enforce class-creation policy or interpret class declarations as a DSL.</p>
  </div>
  <div class="check-card">
    <h3>Bad fit</h3>
    <p>You only need light validation, registration, or attribute rewrites.</p>
  </div>
  <div class="check-card">
    <h3>Tradeoff</h3>
    <p>Metaclasses affect inheritance and composition, so they raise the cost for downstream users.</p>
  </div>
</div>

## Read Before This

- [Data Model](/en/pythonic/data-model)
- [Descriptors and Properties](/en/pythonic/descriptors-and-properties)
