# Typing

<p class="lead">이 파트는 typing을 "mypy를 만족시키는 문법"이 아니라, API와 boundary를 설계하는 도구로 다시 정리한다. Python 3.14 기준의 typing은 `Union`, `Generic`, `Annotated`를 외부 라이브러리 문법처럼 다루던 시절보다 훨씬 언어 중심적이고, 동시에 런타임 metadata와 더 강하게 연결된다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 좋은 typing은 타입 주석을 많이 다는 것이 아니라, 공개 API의 shape를 명확히 하고, narrowing을 안전하게 만들고, 정적 세계와 런타임 metadata의 경계를 분명히 하는 데 있다.</p>
</div>

## 이 파트에서 잡아야 할 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>어떤 타입이 읽기 좋은가</h3>
    <p>`X | Y`, `type` alias, built-in generic syntax를 적절히 쓰면 API 자체가 훨씬 설명적으로 변한다.</p>
  </div>
  <div class="reading-card">
    <h3>언제 generic이 필요한가</h3>
    <p>타입 정보를 유지한 채 재사용 가능한 API를 만들 때 generic은 큰 힘을 발휘한다.</p>
  </div>
  <div class="reading-card">
    <h3>duck typing을 어떻게 타입으로 표현하나</h3>
    <p>`Protocol`은 상속 대신 capability를 기준으로 인터페이스를 표현한다.</p>
  </div>
  <div class="reading-card">
    <h3>정적 타입과 런타임은 어떻게 다른가</h3>
    <p>type checker가 보는 세계와 Pydantic/FastAPI가 annotation을 읽는 방식은 같지 않다.</p>
  </div>
</div>

## 추천 순서

1. [Modern Typing](/typing/modern-typing)
2. [Generics](/typing/generics)
3. [Protocols](/typing/protocols)
4. [Type Narrowing](/typing/type-narrowing)
5. [Runtime vs Static](/typing/runtime-vs-static)

## 실전 연결

- FastAPI request/response contract
- Pydantic `Annotated` metadata와 validation
- SQLAlchemy repository와 service layer API
