# Pythonic

<p class="lead">This section closes the gap between "I know Python syntax" and "I can design code the Python way." Descriptors, decorators, context managers, and metaclasses make much more sense once you see them as layers on top of the data model and attribute lookup rules.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: being Pythonic mostly means understanding the data model and then choosing the smallest tool that fits: descriptor, decorator, context manager, or metaclass. Most framework magic is really just this stack of hooks.</p>
</div>

## Questions This Part Answers

<div class="reading-grid">
  <div class="reading-card">
    <h3>Why `len(obj)`?</h3>
    <p>Python syntax is connected to object protocol methods, not to arbitrary instance method names.</p>
  </div>
  <div class="reading-card">
    <h3>Why do fields feel magical?</h3>
    <p>Descriptors plus attribute lookup order explain ORM fields, computed attributes, and bound methods.</p>
  </div>
  <div class="reading-card">
    <h3>When is a dataclass enough?</h3>
    <p>Dataclasses are excellent for value objects, settings, and internal command payloads. They become painful when asked to own validation, persistence, and transport concerns at once.</p>
  </div>
  <div class="reading-card">
    <h3>Decorator or metaclass?</h3>
    <p>Both extend behavior, but they act at different times and with very different costs.</p>
  </div>
  <div class="reading-card">
    <h3>How do open-source projects stay Pythonic?</h3>
    <p>Read real snippets from Click, Requests, SQLAlchemy, Pydantic, and FastAPI to see how Pythonic design choices are encoded in production code.</p>
  </div>
  <div class="reading-card">
    <h3>How do you express scope?</h3>
    <p>Context managers are the clearest Pythonic way to express resource ownership and cleanup boundaries.</p>
  </div>
</div>

## Recommended Order

1. [Data Model](/en/pythonic/data-model)
2. [Dataclasses](/en/pythonic/dataclasses)
3. [Descriptors and Properties](/en/pythonic/descriptors-and-properties)
4. [Open-source Pythonic Deep Dives](/en/pythonic/opensource-pythonic-patterns)
5. [Decorators](/en/pythonic/decorators)
6. [Context Managers](/en/pythonic/context-managers)
7. [Metaclasses](/en/pythonic/metaclasses)

## Practical Connections

- FastAPI route decorators and dependency wiring
- dataclass-based internal commands and value objects
- Pydantic field annotations and field access behavior
- SQLAlchemy instrumented attributes and class construction hooks
- reading decorator/context manager/factory patterns in real open-source code
