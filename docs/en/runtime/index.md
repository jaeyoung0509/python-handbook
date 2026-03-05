# Runtime

<p class="lead">This section reads CPython as an execution engine. It connects frames, bytecode, the object model, memory management, the GIL, and subinterpreters into one usable picture for performance and architecture decisions.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: once you have runtime intuition, you can replace vague claims like "Python is slow" with concrete ideas such as attribute-lookup cost, reference counting behavior, specialization stability, GIL boundaries, and GC pause tradeoffs.</p>
</div>

## Questions This Part Answers

<div class="reading-grid">
  <div class="reading-card">
    <h3>What does "everything is an object" cost?</h3>
    <p>Object headers, type objects, and slot dispatch explain a lot of attribute-heavy and method-heavy behavior.</p>
  </div>
  <div class="reading-card">
    <h3>When is memory released immediately?</h3>
    <p>CPython uses reference counting for many immediate releases and a separate GC pass for cycles.</p>
  </div>
  <div class="reading-card">
    <h3>What exactly does the GIL restrict?</h3>
    <p>This is the key to choosing between threads, async tasks, processes, and subinterpreters.</p>
  </div>
  <div class="reading-card">
    <h3>Why did Python 3.11+ get faster?</h3>
    <p>Adaptive specialization changes the cost model of hot bytecode paths.</p>
  </div>
  <div class="reading-card">
    <h3>How deep should we go into internals?</h3>
    <p>Use frame/code object, refcount+cycle GC, and `dis`/`ast`/`tracemalloc`/`gc` labs to build layered runtime intuition.</p>
  </div>
</div>

## Recommended Order

1. [Execution Model](/en/runtime/execution-model)
2. [Object Model](/en/runtime/object-model)
3. [Memory and GC](/en/runtime/memory-and-gc)
4. [GIL and Subinterpreters](/en/runtime/gil-and-subinterpreters)
5. [Bytecode and Specialization](/en/runtime/bytecode-and-specialization)
6. [CPython Internals Advanced](/en/runtime/cpython-internals-advanced)
7. [CPython vs Go Runtime](/en/cpython-vs-go-runtime)
