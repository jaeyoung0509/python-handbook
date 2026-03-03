# SQLAlchemy 2.0

<p class="lead">SQLAlchemy를 잘 쓴다는 건 ORM 문법을 많이 아는 것이 아니라, `Session`, transaction, loading strategy, query shape를 정확히 분리해서 다룬다는 뜻이다. 특히 FastAPI 같은 웹 서비스에서는 세션 수명주기와 API 경계를 잘못 잡는 순간 코드가 바로 꼬인다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: SQLAlchemy 2.0에서 가장 먼저 잡아야 할 감각은 "Session은 캐시가 아니라 작업 단위(unit of work)를 수행하는 트랜잭션 경계"라는 점이다. repository는 SQL을 담당하고, commit/rollback은 use case 경계에서만 일어나야 한다.</p>
</div>

## 이 파트에서 진짜 잡아야 할 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>Session은 무엇인가</h3>
    <p>connection holder가 아니라 identity map과 unit of work를 묶는 작업 문맥이다. scope를 짧게 가져가야 한다.</p>
  </div>
  <div class="reading-card">
    <h3>트랜잭션은 어디서 끝내나</h3>
    <p>repository 안이 아니라 use case 또는 service 경계에서 commit/rollback을 통제하는 편이 가장 안전하다.</p>
  </div>
  <div class="reading-card">
    <h3>ORM 객체를 API에 그대로 넘겨도 되나</h3>
    <p>대체로 안 된다. lazy load, serialization, schema 진화가 한 덩어리로 엉키기 때문이다.</p>
  </div>
  <div class="reading-card">
    <h3>Async는 언제 이득인가</h3>
    <p>전체 스택이 async이고 I/O 동시성이 중요한 경우에만 의미가 크다. 세션 공유 규칙은 오히려 더 엄격해진다.</p>
  </div>
  <div class="reading-card">
    <h3>설정은 어디에 맞춰 바꾸나</h3>
    <p>Lambda, Kubernetes, worker, batch는 process lifetime과 connection budget이 다르다. 같은 pool 설정을 복붙하면 바로 문제로 이어진다.</p>
  </div>
</div>

## 추천 읽기 순서

1. [Session and Unit of Work](/sqlalchemy/session-and-unit-of-work)
2. [Deployment and Engine Settings](/sqlalchemy/deployment-and-engine-settings)
3. [Relationships and Loading](/sqlalchemy/relationships-and-loading)
4. [Async SQLAlchemy](/sqlalchemy/async-sqlalchemy)
5. [Core vs ORM](/sqlalchemy/core-vs-orm)
6. [Migrations and Patterns](/sqlalchemy/migrations-and-patterns)

## 이 파트의 실전 규칙

- Session은 요청 또는 use case 범위로 짧게 유지한다.
- repository는 `commit()` 하지 않는다.
- engine과 pool 설정은 배포 환경의 process model에 맞춰 잡는다.
- write path와 read path를 구분해서 로딩 전략과 응답 DTO를 설계한다.
- ORM model, Pydantic schema, domain 개념을 하나의 클래스에 몰아넣지 않는다.
- async라면 `AsyncSession`을 task 간에 공유하지 않는다.

## 같이 읽으면 좋은 페이지

- [FastAPI Project Structure](/fastapi/project-structure)
- [Dependency Injection](/fastapi/dependency-injection)
- [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)
