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
    <h3>이론과 실전은 어디서 만나나</h3>
    <p>descriptor, typing, runtime, asyncio 지식을 실제 API 서비스 설계와 연결하는 관점을 정리한다.</p>
  </div>
</div>

## 추천 읽기 순서

1. [API Service Template](/playbooks/api-service-template)
2. [Testing with Fixtures](/playbooks/testing-with-pytest-fixtures)
3. [FastAPI + Pydantic + SQLAlchemy](/playbooks/fastapi-pydantic-sqlalchemy)
4. [Typing Review Checklist](/playbooks/typing-review-checklist)

## 이 파트의 사용법

- 새 프로젝트를 시작할 때는 `API Service Template`부터 본다.
- fixture, teardown, override cleanup 기준이 필요하면 `Testing with Fixtures`를 바로 본다.
- 이미 FastAPI/SQLAlchemy 프로젝트가 있다면 `FastAPI + Pydantic + SQLAlchemy`를 먼저 본다.
- 팀 코드 리뷰 기준을 만들고 싶다면 `Typing Review Checklist`를 기준 문서로 둔다.

## 같이 읽으면 좋은 페이지

- [FastAPI](/fastapi/)
- [Pydantic](/pydantic/)
- [SQLAlchemy 2.0](/sqlalchemy/)
- [Typing](/typing/)
