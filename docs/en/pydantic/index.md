# Pydantic

<p class="lead">This section reads Pydantic v2 as a validation engine rather than as a pretty model-declaration library. `BaseModel` is only the visible entry point; the real core is `pydantic-core`, core schema generation, `TypeAdapter`, and the distinction between strict and lax behavior.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: to understand Pydantic deeply, start with the flow `annotation -> core schema -> validator/serializer -> DTO`. Once that picture is clear, FastAPI integration, settings parsing, and type-driven API design all become easier to reason about.</p>
</div>

## The Intuition This Part Builds

<div class="reading-grid">
  <div class="reading-card">
    <h3>Look beyond BaseModel</h3>
    <p>`BaseModel` is great for named contracts, but Pydantic's real scope is wider. `TypeAdapter` lets arbitrary types use the same engine.</p>
  </div>
  <div class="reading-card">
    <h3>Separate strict from lax</h3>
    <p>Pydantic often defaults to "parse when reasonable." Knowing where to permit coercion and where to reject it is a real API design decision.</p>
  </div>
  <div class="reading-card">
    <h3>Separate validation from serialization</h3>
    <p>Input rules and output rules are not the same thing. Validators and serializers should not carry the same responsibilities.</p>
  </div>
  <div class="reading-card">
    <h3>See how frameworks consume it</h3>
    <p>FastAPI reads annotations and turns them into Pydantic-driven request and response boundaries. Typing, runtime introspection, and Pydantic are part of one system.</p>
  </div>
</div>

## Recommended Order

1. [Core Schema](/en/pydantic/core-schema)
2. [Validation Pipeline](/en/pydantic/validation-pipeline)
3. [BaseModel vs TypeAdapter](/en/pydantic/basemodel-vs-typeadapter)
4. [Internals](/en/pydantic/internals)

## Practical Rules

- Do not force every validation problem into a `BaseModel`.
- Separate public DTOs from internal adapters.
- Choose strict/lax policy per boundary.
- Use validators for input rules and serializers for output contracts.
