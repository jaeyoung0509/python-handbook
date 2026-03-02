# Bytecode and Specialization

## Why It Matters

Performance work in modern CPython increasingly starts with bytecode, specialization, and hotspot stability rather than with vague "Python is slow" claims.

## This Chapter Builds

- how to read bytecode
- using `dis`
- the adaptive interpreter
- code that specializes well and code that does not
- how the JIT discussion connects to specialization

## Practical Connections

- hot-path profiling
- loop optimization intuition
- function-call and attribute-lookup costs
