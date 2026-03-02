# Runtime

<p class="lead">이 파트는 CPython을 "언어 실행기"로 읽는 섹션이다. Python 코드가 frame과 bytecode 위에서 어떻게 돌고, 객체 모델과 메모리 모델이 어떤 비용 구조를 만들며, GIL과 subinterpreter가 병렬성 선택지를 어떻게 바꾸는지 한 그림으로 연결한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: runtime 감각이 생기면 "Python은 느리다" 같은 막연한 말 대신, attribute lookup 비용, reference counting, specialization, GIL 경계, GC pause, isolation trade-off로 문제를 구체적으로 볼 수 있다.</p>
</div>

## 이 파트에서 잡아야 할 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>모든 값이 객체라는 게 무슨 뜻인가</h3>
    <p>object header, type object, slot dispatch 감각이 있어야 attribute-heavy 코드와 method cost를 읽을 수 있다.</p>
  </div>
  <div class="reading-card">
    <h3>메모리는 언제 바로 해제되나</h3>
    <p>CPython은 refcount로 많은 객체를 즉시 회수하지만, cycle은 별도 GC가 담당한다.</p>
  </div>
  <div class="reading-card">
    <h3>GIL은 정확히 뭘 막나</h3>
    <p>Python bytecode 병렬 실행의 경계와 thread/process/subinterpreter 선택이 여기서 갈린다.</p>
  </div>
  <div class="reading-card">
    <h3>3.11 이후 왜 빨라졌나</h3>
    <p>adaptive interpreter와 specialization이 hot path의 opcode를 더 구체적으로 바꿔주기 때문이다.</p>
  </div>
</div>

## 추천 순서

1. [Execution Model](/runtime/execution-model)
2. [Object Model](/runtime/object-model)
3. [Memory and GC](/runtime/memory-and-gc)
4. [GIL and Subinterpreters](/runtime/gil-and-subinterpreters)
5. [Bytecode and Specialization](/runtime/bytecode-and-specialization)
6. [CPython vs Go Runtime](/cpython-vs-go-runtime)
