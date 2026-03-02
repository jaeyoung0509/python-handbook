# Execution Model

<p class="lead">Python 실행 모델은 "인터프리터가 코드를 한 줄씩 읽는다"보다 훨씬 구체적이다. source를 AST와 code object로 바꾸고, frame 위에서 bytecode를 평가한다는 감각이 있어야 import, closure, late binding, 디버깅 포인트가 한 번에 정리된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Python은 source를 AST와 code object로 바꾼 뒤, frame 안의 namespace와 evaluation stack을 사용해 bytecode를 실행한다. import, scope, closure 문제는 대부분 이 그림에서 풀린다.</p>
</div>

## 먼저 머리에 넣을 그림

<MermaidDiagram
  caption="source code는 바로 '실행'되는 것이 아니라, AST와 code object를 거쳐 frame 위에서 평가된다."
  chart="flowchart LR; A[source.py] --> B[Parser]; B --> C[AST]; C --> D[Compiler]; D --> E[Code Object]; E --> F[Frame]; F --> G[Evaluation Stack]; G --> H[Python Objects and Exceptions];"
/>

## 왜 중요한가

- circular import가 왜 생기는지 import 시점으로 설명할 수 있다.
- closure와 late binding이 왜 생기는지 scope와 cell object로 이해할 수 있다.
- `dis`, traceback, profiler 출력이 훨씬 자연스럽게 읽힌다.

## 실행 흐름을 4단계로 보기

### 1. Parse와 compile

- parser는 source를 AST로 바꾼다.
- compiler는 AST를 code object로 만든다.
- code object는 실행 가능한 명령 묶음이지, 아직 실행 중인 상태는 아니다.

### 2. 이름 바인딩과 scope 결정

- compiler는 어떤 이름이 local, free, cell, global인지 미리 계산한다.
- 그래서 closure는 "나중에 얼추 찾아본다"가 아니라, 특정 scope 슬롯을 가리키는 구조로 동작한다.

### 3. frame 생성

- 함수 호출, 모듈 import, comprehension 같은 실행 단위는 frame을 만든다.
- frame에는 locals, globals, builtins, instruction pointer, evaluation stack 같은 실행 문맥이 들어 있다.

### 4. eval loop가 bytecode 실행

- CPython은 code object 안의 bytecode를 opcode 단위로 실행한다.
- attribute lookup, function call, exception handling도 결국 이 평가 루프 위에서 돌아간다.

## 코드로 보면 더 빨리 잡히는 것

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

print("module code:", module_code)
print("outer closure vars:", outer.__code__.co_freevars)
print("inner closure vars:", inner.__code__.co_freevars)
dis.dis(outer)
dis.dis(inner)
```

<p class="code-caption">이 예제에서 `compile()`은 code object를 만들고, `exec()`가 namespace를 채운다. `inner`는 `z`를 free variable로 잡고 있어서 closure cell을 통해 값에 접근한다.</p>

## 실무에서 특히 도움이 되는 순간

<div class="doc-checklist">
  <div class="check-card">
    <h3>Import cycle</h3>
    <p>모듈 import도 frame에서 실행되므로, "아직 다 초기화되지 않은 모듈"을 참조하는 순간 순환 참조 문제가 드러난다.</p>
  </div>
  <div class="check-card">
    <h3>Late binding</h3>
    <p>루프 안 람다나 closure가 마지막 값을 보는 이유를 cell object와 scope 계산으로 설명할 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>Profiler output</h3>
    <p>frame과 opcode 단위를 알면 traceback, `dis`, profiler 결과가 단순 문자열이 아니라 실행 모델로 읽힌다.</p>
  </div>
</div>

## 체크리스트

- import 시점 부작용이 큰 모듈은 초기화 순서를 의식해서 나눈다.
- closure 버그가 의심되면 free variable과 default argument 캡처를 먼저 본다.
- 런타임 문제를 볼 때는 source만 보지 말고 code object, frame, bytecode까지 생각한다.
