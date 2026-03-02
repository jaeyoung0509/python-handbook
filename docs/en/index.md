---
layout: home

hero:
  name: Python Handbook
  text: Modern Python, rebuilt around Python 3.14
  tagline: A bilingual handbook for Pythonic design, typing, CPython internals, asyncio, FastAPI, Pydantic, and SQLAlchemy 2.0
  actions:
    - theme: brand
      text: Start with Intro
      link: /en/intro/
    - theme: alt
      text: 한국어로 읽기
      link: /

features:
  - title: Bilingual Handbook
    details: Korean lives at the site root and English lives under `/en/`, so you can switch languages without leaving the handbook structure.
  - title: Visual First
    details: Important chapters use quick takeaways, diagrams, and runnable code blocks instead of dense walls of prose.
  - title: Language to Frameworks
    details: The path goes from Pythonic patterns and typing to runtime internals, asyncio, FastAPI, Pydantic, and SQLAlchemy 2.0.
---

## What This Handbook Is

<div class="quick-takeaway">
  <p><strong>Core idea</strong>: this is not a release-note archive. It is a topic-driven handbook that uses Python 3.14 as the baseline and connects language design, runtime behavior, and backend engineering.</p>
</div>

<div class="reading-grid">
  <div class="reading-card">
    <h3>1. Rebuild Pythonic intuition</h3>
    <p>Start with the data model, descriptors, decorators, context managers, and metaclasses before touching framework internals.</p>
  </div>
  <div class="reading-card">
    <h3>2. Use typing as design</h3>
    <p>Treat modern typing as a way to shape APIs and boundaries, not as decorative syntax.</p>
  </div>
  <div class="reading-card">
    <h3>3. See runtime behavior</h3>
    <p>Frames, bytecode, specialization, the GIL, and GC explain many performance and architecture tradeoffs.</p>
  </div>
  <div class="reading-card">
    <h3>4. Apply it to services</h3>
    <p>FastAPI, Pydantic, and SQLAlchemy make more sense once the language and runtime pieces are clear.</p>
  </div>
</div>

## Recommended Entry Points

1. [Intro](/en/intro/) for the map of the handbook.
2. [Execution Model](/en/runtime/execution-model) for how Python code actually runs.
3. [Metaclasses](/en/pythonic/metaclasses) for class creation hooks and alternatives.
4. [FastAPI Project Structure](/en/fastapi/project-structure) for a pragmatic service layout.

## How Chapters Are Written

- Quick takeaway: one sentence you should remember after reading.
- Diagram: a visual model before implementation details.
- Code: practical examples you can run or adapt.
- Checklist: when to use the technique and where it goes wrong.
