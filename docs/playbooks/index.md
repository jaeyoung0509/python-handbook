# Playbooks

<p class="lead">이 파트는 앞선 이론을 실제 서비스 설계 규칙으로 번역하는 섹션이다. Pythonic, typing, runtime, asyncio, FastAPI, Pydantic, SQLAlchemy를 각각 잘 아는 것만으로는 부족하고, 그것들이 한 서비스 안에서 어떻게 연결되어야 덜 꼬이는지가 더 중요하다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: playbook은 "이론 요약"이 아니라 설계 의사결정 기준이다. 새 서비스 뼈대를 만들 때, 코드 리뷰할 때, 기존 구조를 리팩터링할 때 바로 적용할 수 있어야 한다.</p>
</div>

## 이 파트에서 풀려는 질문

<div class="reading-grid">
  <div class="reading-card">
    <h3>처음 서비스 뼈대는 어떻게 잡나</h3>
    <p>router, service, repository, schema, settings, logging, tests를 어디에 두고 어떻게 연결할지 제안한다.</p>
  </div>
  <div class="reading-card">
    <h3>지금 보이는 냄새를 어디서부터 고치나</h3>
    <p>fat route, hidden commit, DTO/ORM collapse 같은 공통 smell을 atlas와 refactoring series로 빠르게 연결한다.</p>
  </div>
  <div class="reading-card">
    <h3>환경변수와 설정은 어떻게 설계하나</h3>
    <p>`settings.py`, `pydantic-settings`, `.env`, secret source, dependency override를 어떤 기준으로 나눌지 정리한다.</p>
  </div>
  <div class="reading-card">
    <h3>FastAPI + Pydantic + SQLAlchemy를 어떻게 덜 꼬이게 붙이나</h3>
    <p>request DTO, transaction, ORM entity, response DTO 경계를 분리해 API가 길게 살아남는 구조를 잡는다.</p>
  </div>
  <div class="reading-card">
    <h3>타입 리뷰는 무엇을 봐야 하나</h3>
    <p>문법 사용 여부보다 `Any` 누수, alias 남용, protocol 설계, boundary 명확성을 먼저 보는 체크리스트를 제공한다.</p>
  </div>
  <div class="reading-card">
    <h3>테스트 fixture는 어떻게 설계하나</h3>
    <p>yield fixture, dependency override cleanup, DB 격리, client lifecycle을 어떻게 나눌지 실전 패턴으로 정리한다.</p>
  </div>
  <div class="reading-card">
    <h3>fixture 다음 테스트 층은 무엇인가</h3>
    <p>HTTP contract, websocket protocol, property-based test, idempotency invariant를 어느 도구로 잡을지 정리한다.</p>
  </div>
  <div class="reading-card">
    <h3>Lambda와 Kubernetes는 어떻게 고르나</h3>
    <p>트래픽 모양, DB 연결 방식, long-lived connection, 운영 표면적을 기준으로 선택하는 틀을 제안한다.</p>
  </div>
  <div class="reading-card">
    <h3>점진 배포 중 schema는 어떻게 안전하게 바꾸나</h3>
    <p>rolling, blue-green, canary, Lambda alias 환경에서 Alembic, backfill, feature flag 순서를 어떻게 잡을지 정리한다.</p>
  </div>
  <div class="reading-card">
    <h3>Schema, API, event는 어떻게 같이 진화시키나</h3>
    <p>DB migration, API versioning, event versioning, backfill/replay를 하나의 contract evolution 관점으로 묶어 본다.</p>
  </div>
  <div class="reading-card">
    <h3>retry와 duplicate delivery는 어떻게 다루나</h3>
    <p>idempotency key, outbox, publisher retry, dedupe를 같은 그림으로 묶어 본다.</p>
  </div>
  <div class="reading-card">
    <h3>이론과 실전은 어디서 만나나</h3>
    <p>descriptor, typing, runtime, asyncio 지식을 실제 API 서비스 설계와 연결하는 관점을 정리한다.</p>
  </div>
</div>

## 추천 읽기 순서

1. [Refactoring Atlas](/playbooks/refactoring-atlas)
2. [API Service Template](/playbooks/api-service-template)
3. [리팩토링: Fat Route와 DI Leakage](/playbooks/refactoring-fat-routes-and-dependency-leakage)
4. [Settings and Pydantic Settings](/playbooks/settings-and-pydantic-settings)
5. [ABC + Fake UoW Testing](/playbooks/testing-abc-and-fake-uow)
6. [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)
7. [리팩토링: Session Ownership과 Hidden Commits](/playbooks/refactoring-session-ownership-and-hidden-commits)
8. [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)
9. [리팩토링: DTO Boundary와 Over-Abstraction](/playbooks/refactoring-dto-boundaries-and-over-abstraction)
10. [Testing with Fixtures](/playbooks/testing-with-pytest-fixtures)
11. [Testing Beyond Fixtures](/playbooks/testing-beyond-fixtures)
12. [Lambda vs Kubernetes](/playbooks/lambda-vs-kubernetes)
13. [Progressive Delivery + Alembic](/playbooks/progressive-delivery-and-alembic)
14. [계약 진화와 지속가능한 CD](/playbooks/contract-evolution-and-sustainable-cd)
15. [Idempotency와 Outbox](/playbooks/idempotency-and-outbox)
16. [Typing Review Checklist](/playbooks/typing-review-checklist)

## 이 파트를 리뷰 관점으로 읽는 법

- 핵심 playbook 끝에는 `Code Review Lens`, `Common Anti-Patterns`, `Likely Discussion Questions`, `Strong Answer Frame` 블록이 붙는다.
- `API Service Template`, `Use Case + UoW + ABC`는 `sub-optimal -> improved` 예제로 설계 리팩터링 방향을 바로 보여준다.
- `Refactoring Atlas`는 공통 냄새를 먼저 찾는 index 역할을 하고, refactoring series는 각 냄새를 narrative하게 깊게 판다.
- `Lambda vs Kubernetes`, `Progressive Delivery + Alembic`은 symptom-first scenario table로 운영 판단 순서를 정리한다.

## 이 파트의 사용법

- 지금 보이는 냄새를 빠르게 분류하고 싶다면 `Refactoring Atlas`부터 본다.
- route와 dependency가 엉켰다면 `리팩토링: Fat Route와 DI Leakage`를 먼저 본다.
- 새 프로젝트를 시작할 때는 `API Service Template`부터 본다.
- 환경 변수, `.env`, secret source, `get_settings()` 경계를 잡고 싶다면 `Settings and Pydantic Settings`를 바로 본다.
- fixture, teardown, override cleanup 기준이 필요하면 `Testing with Fixtures`를 바로 본다.
- fixture 다음 단계로 contract/property/protocol 테스트를 확장하고 싶다면 `Testing Beyond Fixtures`를 바로 본다.
- use case를 DB 없이 빨리 검증하는 테스트가 필요하면 `ABC + Fake UoW Testing`을 본다.
- use case와 SQLAlchemy UoW를 `abc.ABC` 기반 경계와 함께 보고 싶다면 `Use Case + UoW + ABC`를 본다.
- hidden commit이나 split session ownership이 보인다면 `리팩토링: Session Ownership과 Hidden Commits`를 바로 본다.
- 이미 FastAPI/SQLAlchemy 프로젝트가 있다면 `FastAPI + Pydantic + SQLAlchemy`를 먼저 본다.
- DTO/ORM collapse나 과한 ABC가 보인다면 `리팩토링: DTO Boundary와 Over-Abstraction`을 먼저 본다.
- 배포 대상을 Lambda와 Kubernetes 중에서 비교해야 한다면 `Lambda vs Kubernetes`를 본다.
- rolling, blue-green, canary, Lambda alias 배포에서 Alembic과 backfill 순서를 잡고 싶다면 `Progressive Delivery + Alembic`을 본다.
- DB schema, public API, async event를 한 묶음의 contract evolution 문제로 정리하고 싶다면 `계약 진화와 지속가능한 CD`를 본다.
- retry-safe create API, idempotency key, outbox publish를 같이 설계하고 싶다면 `Idempotency와 Outbox`를 본다.
- 팀 코드 리뷰 기준을 만들고 싶다면 `Typing Review Checklist`를 기준 문서로 둔다.

## 같이 읽으면 좋은 페이지

- [FastAPI](/fastapi/)
- [Pydantic](/pydantic/)
- [SQLAlchemy 2.0](/sqlalchemy/)
- [Typing](/typing/)
