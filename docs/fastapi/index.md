# FastAPI

<p class="lead">이 파트는 FastAPI를 "빠르게 API를 여는 프레임워크"로만 보지 않고, 비동기 Python 서비스에서 boundary를 어떻게 설계해야 오래 가는지를 중심으로 다룬다. route, dependency, Pydantic schema, service, SQLAlchemy session이 어디서 만나고 어디서 끊어져야 하는지가 핵심이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: FastAPI를 잘 쓴다는 것은 endpoint 함수 안에서 모든 일을 처리하는 것이 아니라, HTTP boundary와 application boundary를 분리하고, request scope 자원 수명주기를 명확히 관리하고, DTO 계약을 안정적으로 유지하는 것이다.</p>
</div>

## 이 파트에서 먼저 잡아야 할 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>route는 어디까지 알아야 하나</h3>
    <p>HTTP 파싱, 인증, 응답 계약까지만 책임지고 도메인 규칙과 commit 정책은 안쪽으로 넘기는 편이 안정적이다.</p>
  </div>
  <div class="reading-card">
    <h3>dependency는 무엇을 해야 하나</h3>
    <p>세션, 설정, 외부 클라이언트 같은 리소스 wiring을 맡고, business branching은 service에 남겨둬야 한다.</p>
  </div>
  <div class="reading-card">
    <h3>async라고 자동으로 빨라지나</h3>
    <p>아니다. blocking 호출, validation cost, DB pool 설정, worker 수, 응답 직렬화 비용이 더 자주 병목이 된다.</p>
  </div>
  <div class="reading-card">
    <h3>테스트는 무엇을 검증해야 하나</h3>
    <p>단순 상태 코드보다 lifespan 자원 초기화, dependency override, transaction 격리, serialization 경계를 먼저 검증해야 한다.</p>
  </div>
</div>

## 추천 읽기 순서

1. [Project Structure](/fastapi/project-structure)
2. [Dependency Injection](/fastapi/dependency-injection)
3. [Request/Response Modeling](/fastapi/request-response-modeling)
4. [Lifespan and Testing](/fastapi/lifespan-and-testing)
5. [Performance and Ops](/fastapi/performance-and-ops)

## FastAPI 파트의 실전 규칙

- route는 transport adapter처럼 얇게 유지한다.
- request DTO, domain command, ORM entity, response DTO를 한 타입으로 합치지 않는다.
- `yield` dependency 또는 lifespan으로 자원 수명주기를 닫는다.
- endpoint는 `async`라고 해서 sync I/O를 숨기지 않는다.
- 성능 문제는 프레임워크보다 query shape, serialization, pool, worker model에서 먼저 찾는다.

## 같이 읽으면 좋은 페이지

- [Asyncio](/asyncio/)
- [Pydantic](/pydantic/)
- [SQLAlchemy 2.0](/sqlalchemy/)
- [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)
