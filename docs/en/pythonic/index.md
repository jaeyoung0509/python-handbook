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
    <h3>Decorator or metaclass?</h3>
    <p>Both extend behavior, but they act at different times and with very different costs.</p>
  </div>
  <div class="reading-card">
    <h3>How do you express scope?</h3>
    <p>Context managers are the clearest Pythonic way to express resource ownership and cleanup boundaries.</p>
  </div>
</div>

## Recommended Order

1. [Data Model](/en/pythonic/data-model)
2. [Descriptors and Properties](/en/pythonic/descriptors-and-properties)
3. [Decorators](/en/pythonic/decorators)
4. [Context Managers](/en/pythonic/context-managers)
5. [Metaclasses](/en/pythonic/metaclasses)

## Practical Connections

- FastAPI route decorators and dependency wiring
- Pydantic field annotations and field access behavior
- SQLAlchemy instrumented attributes and class construction hooks
