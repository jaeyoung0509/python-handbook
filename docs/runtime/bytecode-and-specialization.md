# Bytecode and Specialization

<p class="lead">Python 3.11 이후 성능을 이야기할 때는 적응형 특수화를 빼고 말하기 어렵다. CPython은 단순히 bytecode를 해석하는 것에서 더 나아가, 실행 중 관찰한 패턴을 바탕으로 opcode를 더 특화된 형태로 바꾸며 hot path를 줄여간다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 현대 CPython 성능은 "인터프리터라 느리다"보다 "어떤 bytecode가 얼마나 안정적으로 specialization될 수 있나"로 보는 편이 더 정확하다. `dis`를 읽을 줄 알면 hot path 감각이 크게 좋아진다.</p>
</div>

## specialization 흐름

<MermaidDiagram
  caption="코드는 먼저 일반 opcode로 시작하고, 실행 중 패턴이 안정되면 더 구체적인 specialized opcode로 바뀔 수 있다."
  chart="flowchart LR; A[source code] --> B[bytecode]; B --> C[adaptive interpreter]; C --> D[specialized opcodes and inline caches]; D --> E[faster hot path];"
/>

## `dis`로 specialization 보기

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

<p class="code-caption">처음에는 일반 opcode로 시작하지만, 같은 형태의 attribute access와 loop가 반복되면 adaptive interpreter가 더 특화된 opcode와 cache를 붙일 수 있다. `adaptive=True`, `show_caches=True`를 켜면 이런 힌트를 더 잘 볼 수 있다.</p>

## specialization이 잘 되는 코드 감각

- 객체 형태와 연산 패턴이 비교적 안정적일 때
- attribute access 대상 type이 자주 바뀌지 않을 때
- hot loop 안에서 같은 연산이 반복될 때

## specialization이 잘 안 되는 경우

- 너무 동적이고 shape가 자주 바뀌는 객체
- monkey patch가 많고 전역/속성 구조가 자주 변하는 코드
- hot path보다 함수 경계와 I/O가 더 지배적인 코드

## JIT와의 연결

- specialization은 JIT와 별개지만, 더 공격적인 최적화의 기반 정보를 제공한다
- 지금 CPython의 성능 이야기는 JIT보다 specialization이 먼저 체감되는 경우가 많다
- 따라서 실무에서는 먼저 bytecode와 specialization 감각을 잡는 편이 더 유효하다

## 실전 연결

- hot path profiling
- Python loop 최적화 감각
- function call / attribute lookup cost 감각

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>`dis`를 읽는다</h3>
    <p>성능 문제를 볼 때는 source만 보지 말고 bytecode와 cache 힌트도 같이 본다.</p>
  </div>
  <div class="check-card">
    <h3>shape stability를 본다</h3>
    <p>객체 구조와 access 패턴이 안정적일수록 specialization이 유리하다.</p>
  </div>
  <div class="check-card">
    <h3>과한 미세 최적화는 피한다</h3>
    <p>특수화가 좋아졌다고 해서 가독성을 버리는 미세 최적화를 기본 전략으로 삼을 필요는 없다.</p>
  </div>
  <div class="check-card">
    <h3>I/O와 호출 경계를 같이 본다</h3>
    <p>hot loop가 아닌 시스템에서는 specialization보다 I/O, allocation, DB round trip이 더 큰 병목일 수 있다.</p>
  </div>
</div>

## 공식 자료

- [dis](https://docs.python.org/3/library/dis.html)
- [PEP 659: Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/)
