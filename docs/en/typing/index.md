# Typing

<p class="lead">This section treats typing as an API and boundary design tool, not as a side quest for pleasing a type checker. In Python 3.14, typing is more language-shaped than it used to be, and it is also more deeply connected to runtime metadata consumers such as FastAPI and Pydantic.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: good typing is not about adding more annotations. It is about making public API shapes clear, making narrowing safe, and keeping the boundary between static meaning and runtime metadata explicit.</p>
</div>

## Questions This Part Answers

<div class="reading-grid">
  <div class="reading-card">
    <h3>Which types read well?</h3>
    <p>`X | Y`, `type` aliases, and built-in generics can make APIs much more readable.</p>
  </div>
  <div class="reading-card">
    <h3>When do generics matter?</h3>
    <p>Generics keep reusable APIs from losing concrete type information.</p>
  </div>
  <div class="reading-card">
    <h3>How do you type duck typing?</h3>
    <p>`Protocol` lets you describe capabilities without forcing inheritance.</p>
  </div>
  <div class="reading-card">
    <h3>How do static and runtime views differ?</h3>
    <p>Type checkers and runtime frameworks consume annotations for different reasons and in different ways.</p>
  </div>
</div>

## Recommended Order

1. [Modern Typing](/en/typing/modern-typing)
2. [Generics](/en/typing/generics)
3. [Protocols](/en/typing/protocols)
4. [Type Narrowing](/en/typing/type-narrowing)
5. [Runtime vs Static](/en/typing/runtime-vs-static)

## Practical Connections

- FastAPI request and response contracts
- Pydantic `Annotated` metadata and validation
- SQLAlchemy repositories and service-layer APIs
