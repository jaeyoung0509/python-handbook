# Refactoring Atlas

<p class="lead">이 페이지는 서비스 코드에서 반복해서 보이는 공통 냄새를 빠르게 찾기 위한 atlas다. 목표는 "모든 리팩터링을 여기서 끝내기"가 아니라, 지금 보이는 냄새가 어떤 실패 모드로 이어지고 어디서부터 안전하게 고쳐야 하는지 바로 판단하게 만드는 것이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: architecture-first 리팩터링의 핵심은 큰 재설계가 아니라 ownership을 선명하게 복구하는 것이다. route는 transport로, dependency는 wiring으로, service/use case는 business action으로, repository는 persistence detail로, DTO는 외부 계약으로 다시 정렬하면 대부분의 냄새가 줄어든다.</p>
</div>

## 한눈에 보는 atlas

| smell | first safe move | go deeper next |
| --- | --- | --- |
| fat route | route에서 business branching과 commit을 먼저 뺀다 | [Refactoring Fat Routes and Dependency Leakage](/playbooks/refactoring-fat-routes-and-dependency-leakage) |
| dependency leakage | dependency를 resource wiring만 하도록 되돌린다 | [Dependency Injection](/fastapi/dependency-injection) |
| hidden commit | repository/helper에서 commit을 제거하고 service/use case로 올린다 | [Refactoring Session Ownership and Hidden Commits](/playbooks/refactoring-session-ownership-and-hidden-commits) |
| split session ownership | session을 누가 열고 닫는지 한 경계로 통일한다 | [Session and Unit of Work](/sqlalchemy/session-and-unit-of-work) |
| DTO/ORM boundary collapse | request/response DTO와 ORM entity를 먼저 분리한다 | [Refactoring DTO Boundaries and Over-Abstraction](/playbooks/refactoring-dto-boundaries-and-over-abstraction) |
| env/settings lookup in service | `os.getenv()`를 wiring/settings provider로 밀어낸다 | [Settings and Pydantic Settings](/playbooks/settings-and-pydantic-settings) |
| over-abstracted ABCs | substitution 가치가 없는 ABC/generic repository부터 걷어낸다 | [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc) |
| import-time side effects | app factory/lifespan으로 initialization을 모은다 | [API Service Template](/playbooks/api-service-template) |

## 1) Fat Route

- `typical symptom`: route가 validation, auth, query, commit, serialization, feature flag를 모두 처리한다.
- `why it hurts`: HTTP 테스트가 business rule 테스트까지 떠안고, tracing/timeout/retry 위치도 흐려진다.
- `first safe refactor move`: route에서 business branching과 commit만 먼저 service/use case로 이동한다.
- `what not to do`: 처음부터 모든 route를 한 번에 계층 분해하려고 한다.
- `where to go deeper next`: [Refactoring Fat Routes and Dependency Leakage](/playbooks/refactoring-fat-routes-and-dependency-leakage), [Project Structure](/fastapi/project-structure)

## 2) Dependency Injection Leakage

- `typical symptom`: dependency가 feature flag를 읽고, 권한 분기를 하고, commit이나 외부 API 호출까지 한다.
- `why it hurts`: DI가 framework wiring이 아니라 숨은 business layer가 돼 override와 재사용이 비싸진다.
- `first safe refactor move`: dependency는 session/settings/principal/client 조립만 하고 branching은 service로 되돌린다.
- `what not to do`: cleanup이 필요한 자원과 단순 객체 생성을 같은 dependency 성격으로 다룬다.
- `where to go deeper next`: [Refactoring Fat Routes and Dependency Leakage](/playbooks/refactoring-fat-routes-and-dependency-leakage), [Dependency Injection](/fastapi/dependency-injection)

## 3) Hidden Commit Inside Repository or Helper

- `typical symptom`: repository `save()`나 helper 함수가 내부에서 `commit()`을 호출한다.
- `why it hurts`: 하나의 business action 안에서 partial commit이 생기고 rollback reasoning이 어려워진다.
- `first safe refactor move`: repository는 `add()`/query만 남기고 commit은 service/use case 경계로 올린다.
- `what not to do`: `max_overflow`를 키우듯 commit 위치도 임시로 여기저기 늘려 문제를 덮는다.
- `where to go deeper next`: [Refactoring Session Ownership and Hidden Commits](/playbooks/refactoring-session-ownership-and-hidden-commits), [Session and Unit of Work](/sqlalchemy/session-and-unit-of-work)

## 4) Split Session Ownership

- `typical symptom`: request dependency가 live session을 열고, service helper나 UoW가 또 다른 session을 연다.
- `why it hurts`: 같은 use case처럼 보이는데 transaction이 둘로 갈라지고 stale state나 lost update 이해가 어려워진다.
- `first safe refactor move`: 한 request/use case/job에서 session을 누가 열고 닫는지 ownership을 하나로 통일한다.
- `what not to do`: session factory, live session, UoW를 한 흐름에 모두 섞는다.
- `where to go deeper next`: [Refactoring Session Ownership and Hidden Commits](/playbooks/refactoring-session-ownership-and-hidden-commits), [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)

## 5) DTO / ORM Boundary Collapse

- `typical symptom`: request schema, response schema, ORM entity가 사실상 같은 타입으로 취급된다.
- `why it hurts`: persistence 변경이 API contract를 흔들고, serializer 단계에서 lazy load가 새어 나온다.
- `first safe refactor move`: request DTO, response DTO, ORM entity를 최소한 세 타입으로 다시 분리한다.
- `what not to do`: `from_attributes=True` 하나로 boundary collapse를 정당화한다.
- `where to go deeper next`: [Refactoring DTO Boundaries and Over-Abstraction](/playbooks/refactoring-dto-boundaries-and-over-abstraction), [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)

## 6) Env / Settings Lookup Inside Service

- `typical symptom`: service 내부에 `os.getenv()`, `.env` 전제, secret lookup가 흩어져 있다.
- `why it hurts`: 테스트에서 설정 대체가 어려워지고 runtime 환경 차이가 service branching에 바로 새어 들어온다.
- `first safe refactor move`: settings object를 wiring에서 주입하고 service는 이미 해석된 설정만 받게 한다.
- `what not to do`: env lookup을 helper 함수로 감싸서 service 어디서든 부르게 둔다.
- `where to go deeper next`: [API Service Template](/playbooks/api-service-template), [Settings and Pydantic Settings](/playbooks/settings-and-pydantic-settings)

## 7) Over-Abstracted ABCs or Generic Repositories

- `typical symptom`: repository, service, DTO, mapper까지 전부 ABC 또는 generic interface 뒤에 숨어 있다.
- `why it hurts`: 코드가 읽히지 않고 query shape나 transaction ownership 같은 중요한 concrete detail이 사라진다.
- `first safe refactor move`: substitution/testing 가치가 없는 abstraction부터 concrete로 되돌린다.
- `what not to do`: "SOLID니까"라는 이유만으로 모든 계층을 추상화한다.
- `where to go deeper next`: [Refactoring DTO Boundaries and Over-Abstraction](/playbooks/refactoring-dto-boundaries-and-over-abstraction), [Use Case + UoW + ABC](/playbooks/usecase-uow-and-abc)

## 8) Import-Time Side Effects in App Wiring

- `typical symptom`: import만 해도 DB client, tracer, external SDK, router wiring이 실행된다.
- `why it hurts`: 테스트 격리와 startup/shutdown reasoning이 무너지고 app factory가 의미를 잃는다.
- `first safe refactor move`: initialization을 app factory, lifespan, bootstrap 함수로 명시적으로 모은다.
- `what not to do`: side effect를 없애지 않고 import 순서만 조정해 문제를 피한다.
- `where to go deeper next`: [API Service Template](/playbooks/api-service-template), [Project Structure](/fastapi/project-structure)

## 추천 읽기 흐름

1. 전체 냄새를 빠르게 훑고 싶으면 이 atlas부터 본다.
2. route/DI 냄새가 크면 [Refactoring Fat Routes and Dependency Leakage](/playbooks/refactoring-fat-routes-and-dependency-leakage)로 간다.
3. transaction/session 냄새가 크면 [Refactoring Session Ownership and Hidden Commits](/playbooks/refactoring-session-ownership-and-hidden-commits)로 간다.
4. DTO/ORM/ABC 경계가 흐리면 [Refactoring DTO Boundaries and Over-Abstraction](/playbooks/refactoring-dto-boundaries-and-over-abstraction)로 간다.
