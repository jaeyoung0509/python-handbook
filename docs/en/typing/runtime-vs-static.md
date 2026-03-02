# Runtime vs Static

## Why It Matters

The type checker and the runtime do not see the same world. That difference drives many surprises in FastAPI, Pydantic, and metaprogramming.

## This Chapter Builds

- what the type checker sees
- how the runtime reads annotations
- `Annotated` metadata
- `annotationlib`
- how FastAPI and Pydantic consume annotations

## Key Questions

- Why do type checkers know things the runtime does not?
- Which parts of an annotation are types and which parts are metadata?
