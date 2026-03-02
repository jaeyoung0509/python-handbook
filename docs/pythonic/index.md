# Pythonic

<p class="lead">이 파트는 "Python 문법을 안다"와 "Python답게 설계할 수 있다" 사이의 차이를 메우는 섹션이다. descriptor, decorator, context manager, metaclass는 따로따로 배우면 산만하지만, 실제로는 전부 data model과 attribute lookup 위에 서 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Pythonic하다는 말의 핵심은 data model을 이해하고, 그 위에서 attribute lookup, descriptor, decorator, context manager, metaclass를 적절한 크기의 도구로 쓰는 것이다. 프레임워크의 "마법"도 대부분 이 조합이다.</p>
</div>

## 이 파트에서 잡아야 할 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>왜 `len(obj)`인가</h3>
    <p>Python 문법은 객체의 dunder method와 연결된다. 문법과 객체 모델이 분리되어 있지 않다.</p>
  </div>
  <div class="reading-card">
    <h3>왜 필드가 마법처럼 보이나</h3>
    <p>descriptor와 attribute lookup 순서를 알면 ORM, validation framework, computed field가 어떻게 동작하는지 읽힌다.</p>
  </div>
  <div class="reading-card">
    <h3>언제 dataclass면 충분한가</h3>
    <p>값 객체, 설정 객체, 내부 command payload처럼 "가벼운 구조체"가 필요할 때 dataclass가 매우 강하다. 반면 validation과 persistence까지 맡기려 들면 금방 무거워진다.</p>
  </div>
  <div class="reading-card">
    <h3>언제 decorator를 쓰고 언제 metaclass를 쓰나</h3>
    <p>둘 다 확장 도구지만, 개입 시점과 비용이 다르다. 작은 도구부터 쓰는 기준이 중요하다.</p>
  </div>
  <div class="reading-card">
    <h3>자원 경계는 어떻게 표현하나</h3>
    <p>context manager는 Python에서 scope와 cleanup을 가장 명확하게 표현하는 방식이다.</p>
  </div>
</div>

## 추천 순서

1. [Data Model](/pythonic/data-model)
2. [Dataclasses](/pythonic/dataclasses)
3. [Descriptors and Properties](/pythonic/descriptors-and-properties)
4. [Decorators](/pythonic/decorators)
5. [Context Managers](/pythonic/context-managers)
6. [Metaclasses](/pythonic/metaclasses)

## 실전 연결

- FastAPI route decorator와 dependency wiring
- dataclass 기반 내부 command / value object
- Pydantic field annotation과 descriptor-like field access
- SQLAlchemy instrumented attribute와 class construction
