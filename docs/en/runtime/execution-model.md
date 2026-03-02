# Execution Model

<p class="lead">"Python is interpreted" is true but not very helpful. The useful model is: source becomes an AST, the AST becomes a code object, and the code object runs inside frames that execute bytecode against Python objects.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: most import problems, closure surprises, and debugging questions become easier once you can picture code objects, frames, scopes, and the evaluation stack.</p>
</div>

## Keep This Picture In Your Head

<MermaidDiagram
  caption="Python does not execute source text directly. It compiles source into code objects and evaluates them inside frames."
  chart="flowchart LR; A[source.py] --> B[Parser]; B --> C[AST]; C --> D[Compiler]; D --> E[Code Object]; E --> F[Frame]; F --> G[Evaluation Stack]; G --> H[Python Objects and Exceptions];"
/>

## Why It Matters

- Circular imports are really execution-order problems.
- Closures and late binding are scope-layout problems.
- Tracebacks, `dis`, and profilers make more sense once you know what a frame is doing.

## The Four-Step Model

### 1. Parse and compile

- The parser builds an AST from source.
- The compiler turns that AST into a code object.
- A code object is executable metadata, not a running frame.

### 2. Decide scopes and bindings

- The compiler decides which names are local, global, free, or cell variables.
- Closures work because the runtime knows which slots need to outlive the current frame.

### 3. Create frames

- Function calls, module imports, and other execution units create frames.
- A frame carries locals, globals, builtins, an instruction pointer, and the evaluation stack.

### 4. Run the eval loop

- CPython executes bytecode instruction by instruction.
- Attribute access, function calls, and exception handling are all driven by this loop.

## A Small Example

```py
import dis

source = """
x = 10

def outer(y):
    z = x + y

    def inner():
        return z * 2

    return inner
"""

module_code = compile(source, "demo.py", "exec")
namespace: dict[str, object] = {}
exec(module_code, namespace)

outer = namespace["outer"]
inner = outer(5)

print("outer free vars:", outer.__code__.co_freevars)
print("inner free vars:", inner.__code__.co_freevars)
dis.dis(outer)
dis.dis(inner)
```

<p class="code-caption">`compile()` gives you a code object. `exec()` runs it in a namespace. The nested function keeps `z` alive through closure cells, which is why late binding and closure behavior are runtime-model questions.</p>

## Where This Pays Off

<div class="doc-checklist">
  <div class="check-card">
    <h3>Import cycles</h3>
    <p>Modules execute top to bottom, so partially initialized modules are part of the model, not a weird edge case.</p>
  </div>
  <div class="check-card">
    <h3>Closure bugs</h3>
    <p>Loop-variable capture and default-argument workarounds make sense once you think in free variables and cells.</p>
  </div>
  <div class="check-card">
    <h3>Performance reading</h3>
    <p>Bytecode and frames help you read profiler output as runtime behavior instead of as raw text.</p>
  </div>
</div>

## Checklist

- Treat import-time side effects as part of the execution model.
- If a closure looks wrong, inspect free variables before changing the design.
- When runtime behavior is surprising, think about code objects and frames, not just source lines.
