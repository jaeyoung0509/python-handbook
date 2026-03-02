# Bytecode and Specialization

<p class="lead">Since Python 3.11, it is hard to discuss CPython performance without talking about adaptive specialization. CPython now observes runtime patterns and can rewrite hot opcode paths into more specialized forms.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: modern CPython performance is better understood as "which bytecode paths specialize well and stay stable" than as a generic "interpreted languages are slow" story. Learning to read `dis` is one of the highest-leverage runtime skills.</p>
</div>

## Specialization Flow

<MermaidDiagram
  caption="Execution begins with generic bytecode, then adaptive machinery can turn stable hotspots into specialized opcode paths."
  chart="flowchart LR; A[source code] --> B[bytecode]; B --> C[adaptive interpreter]; C --> D[specialized opcodes and inline caches]; D --> E[faster hot path];"
/>

## Use `dis` to See the Change

```py
import dis


class User:
    def __init__(self, age: int) -> None:
        self.age = age


def total_age(users: list[User]) -> int:
    total = 0
    for user in users:
        total += user.age
    return total


items = [User(10), User(20), User(30)]
for _ in range(20_000):
    total_age(items)

dis.dis(total_age, adaptive=True, show_caches=True)
```

<p class="code-caption">The function starts with generic opcodes. Repeated stable execution gives the adaptive interpreter enough signal to attach caches and specialize some operations.</p>

## What Tends to Specialize Well

- stable object shapes
- repeated attribute access on predictable types
- hot loops with repeated operations

## What Tends to Specialize Poorly

- highly dynamic objects whose shape changes often
- heavy monkey patching and frequently changing globals
- code dominated by I/O or cross-boundary calls instead of hot bytecode paths

## How This Relates to JIT

- specialization is not the same as a JIT
- but it provides a more optimized interpreter path and useful runtime information
- in real CPython performance work today, specialization usually matters sooner than JIT experiments

## Practical Connections

- hot-path profiling
- loop optimization intuition
- function-call and attribute-lookup costs

## Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Read `dis` output</h3>
    <p>Source code alone is not always enough for understanding hot-path behavior.</p>
  </div>
  <div class="check-card">
    <h3>Watch shape stability</h3>
    <p>Stable object layouts and access patterns help specialization.</p>
  </div>
  <div class="check-card">
    <h3>Avoid blind micro-optimization</h3>
    <p>Specialization is useful, but readability should still dominate until measurement shows a real hotspot.</p>
  </div>
  <div class="check-card">
    <h3>Profile the real bottleneck</h3>
    <p>Many applications are dominated by I/O, allocation, or DB cost rather than by raw bytecode dispatch.</p>
  </div>
</div>

## Official Sources

- [dis](https://docs.python.org/3/library/dis.html)
- [PEP 659: Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/)
