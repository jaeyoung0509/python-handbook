# 계약 진화와 지속가능한 CD

<p class="lead">스키마 변경이 잦은 시스템에서 진짜 어려운 문제는 Alembic 명령 몇 개가 아니다. 운영 DB schema, public API, async event, historical data는 서로 다른 속도로 진화한다. 이 구분이 흐려지면 팀은 API 버전을 불필요하게 올리고, dual write를 위험하게 남발하고, backfill을 잘못된 계층에서 처리하게 된다. 이 페이지는 versioning을 남발하지 않으면서도 CD를 계속 굴릴 수 있게 만드는 계약 진화 기준을 정리한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 지속가능한 CD의 핵심은 "모든 참여자가 동시에 업그레이드하지 않아도 되게" 만드는 것이다. 기본형은 `additive DB expand -> compatibility app deploy -> additive API/event adapter or version bridge -> resumable backfill or replay -> feature flag cutover -> later contract`다.</p>
</div>

<MermaidDiagram
  caption="지속가능한 CD는 DB schema, API contract, event contract를 같은 문제로 섞지 않고 각 경계별로 호환성을 따로 관리하는 데서 시작한다."
  chart="flowchart LR; A[&quot;clients v1 and v2&quot;] --> B[&quot;API boundary adapter&quot;]; B --> C[&quot;core service&quot;]; C --> D[&quot;expanded DB schema&quot;]; C --> E[&quot;outbox&quot;]; E --> F[&quot;event bridge or v2 event&quot;]; D --> G[&quot;backfill or rebuild&quot;]; F --> H[&quot;old and new consumers&quot;]; G --> I[&quot;cutover and later contract&quot;];"
/>

## 1) 먼저 구분해야 할 세 가지 계약

| 계약 | 주 소비자 | 깨지는 변화 예시 | 기본 대응 |
| --- | --- | --- | --- |
| DB schema | old/new app 버전, batch job, admin script | column drop, rename, constraint 강화 | expand/contract, dual read/write, backfill |
| Sync API contract | 모바일 앱, 외부 고객, frontend | 필드 삭제, 의미 변경, required field 추가 | additive change 우선, boundary adapter, 필요 시 API version |
| Async event contract | consumer service, data pipeline, webhook receiver | event 의미 변경, required field 추가, ordering key 변경 | additive event, upcaster/downcaster, 새 event type 또는 v2 |

이 세 가지를 한 문제로 취급하면 아래 오해가 생긴다.

- DB column rename이 곧바로 public API version bump로 이어진다.
- event payload 변경을 단순 API DTO 수정처럼 생각한다.
- backfill이 필요한 문제를 "코드만 배포하면 해결된다"고 본다.

실제로는 각 계약마다 호환성을 지켜야 하는 상대와 관찰 기간이 다르다.

## 2) versioning보다 먼저 물어야 할 질문

버전을 올리기 전에 아래를 먼저 묻는 편이 낫다.

1. 이 변화는 additive하게 풀 수 있는가
2. old client 또는 old consumer가 잠시라도 살아 있을 수 있는가
3. historical data를 새 계약에 맞춰 바꿔야 하는가
4. 의미가 바뀌는가, 아니면 표현만 바뀌는가

가장 중요한 기준은 이것이다.

- 표현만 바뀌고 의미가 유지되면 version 없이 adapter나 additive change로 버틸 수 있는 경우가 많다.
- 의미가 바뀌면 새 version 또는 새 event type이 필요할 가능성이 크다.

## 3) 상황별 빠른 결정표

| 상황 | DB 전략 | API 전략 | Event 전략 | Data 작업 |
| --- | --- | --- | --- | --- |
| 내부 column rename (`full_name -> display_name`) | expand -> dual read/write -> contract | 보통 version 불필요 | 필요 없으면 그대로 | backfill |
| public response에 새 optional field 추가 | additive column 또는 projection | version 없이 필드 추가 | 필요 시 additive field | 보통 없음 |
| public field 이름 제거 또는 의미 변경 | DB와 분리해서 단계화 | deprecation 후 version 또는 transition field | 관련 event도 의미 바뀌면 새 type 고려 | 경우에 따라 backfill |
| event에 optional field 추가 | additive schema | API 무관 | 기존 event 유지 가능 | 보통 없음 |
| event 의미 변경 (`order.created`의 의미가 달라짐) | 필요 시 별도 DB 변경 | API와 별개로 판단 | 새 event type 또는 `v2` | replay 또는 bridge 필요 가능 |
| 파생 read model 구조 변경 | source-of-truth 유지 | API adapter 또는 projection 전환 | event log 유지 | rebuild/replay가 backfill보다 적합할 수 있음 |

즉, "변화가 생겼다 = 무조건 새 version"은 좋은 기본값이 아니다.

## 4) DB schema 진화: Alembic은 시작점이고 rollout discipline이 본체다

이 저장소의 [Progressive Delivery + Alembic](/playbooks/progressive-delivery-and-alembic)과 [Alembic과 Zero-Downtime Migration](/sqlalchemy/alembic-and-zero-downtime)에서 이미 다루듯, shared DB 시스템의 기본형은 `expand -> backfill -> contract`다.

여기서 전략을 구분하면 더 명확해진다.

| 전략 | 언제 쓰나 | 왜 쓰나 | 비용 |
| --- | --- | --- | --- |
| expand/contract | old/new app이 함께 사는 배포 | destructive change를 뒤로 미루기 위해 | 릴리스가 늘어난다 |
| dual read | 새 데이터와 옛 데이터 표현이 공존 | cutover 전 읽기 호환성 확보 | 읽기 로직이 잠시 복잡해진다 |
| dual write | old/new storage shape를 같이 채워야 함 | backfill과 cutover를 분리하기 위해 | drift 방지가 필요하다 |
| 별도 backfill job | data volume이 크고 resume가 필요 | DDL과 운영성격을 분리하기 위해 | worker/metrics/checkpoint가 필요하다 |
| lazy backfill | hot row만 천천히 갱신해도 됨 | 전체 일괄 작업 비용을 줄이기 위해 | 일관성 수렴 시간이 길어진다 |
| rebuild/replay | 파생 projection이나 read model | source-of-truth에서 다시 만드는 편이 더 안전 | 재생 시간과 infra 비용이 든다 |

중요한 구분:

- 같은 DB transaction 안에서 old/new column에 함께 쓰는 것은 실용적인 dual write다.
- DB commit과 broker publish를 각각 따로 하는 dual write는 위험하다. 이 경우는 [Idempotency와 Outbox](/playbooks/idempotency-and-outbox)처럼 outbox가 더 맞다.

## 5) API versioning: 내부가 아니라 boundary를 version한다

좋은 기본값은 "core service는 versionless, boundary adapter만 version-aware"다.

즉:

- route나 serializer에서 `v1`, `v2`를 구분한다.
- service/use case는 가능한 한 같은 domain model을 유지한다.
- version마다 business logic를 포크하기보다, request/response translation을 둔다.

### API version을 꼭 고려해야 하는 때

- 외부 client가 길게 살아남는다.
- 필드 삭제 또는 의미 변경처럼 명백한 breaking change가 있다.
- deprecation window가 길고, 소비자 업그레이드를 통제할 수 없다.

### 굳이 version을 올리지 않는 편이 좋은 때

- optional field 추가
- 새 endpoint 추가
- 응답에 additive field 추가
- old representation을 잠시 유지할 수 있는 rename

### scheme 선택 기준

| 방식 | 언제 맞나 | 장점 | 단점 |
| --- | --- | --- | --- |
| path version (`/v1/...`) | 외부 공개 API, 문서/게이트웨이 분리 중요 | 가장 눈에 잘 띄고 운영이 단순 | URL 구조가 고정된다 |
| header version | URL 안정성이 중요하고 같은 resource를 유지하고 싶음 | 깔끔한 URL 유지 | 테스트/문서화가 다소 번거롭다 |
| query version | 간단한 전환기 또는 레거시 게이트웨이 | 도입이 쉽다 | URL 오염과 일관성 저하 |
| 날짜 기반 version | SaaS/public API, 긴 deprecation 정책 | 변경 시점을 명확히 기록 | 팀이 version semantics를 엄격히 관리해야 한다 |

핵심은 version scheme보다 운영 원칙이다. API version을 올려도 core service까지 `v1_service`, `v2_service`로 쪼개지면 유지비가 급격히 오른다.

## 6) Event versioning: 가장 늦게, 가장 오래 아픈 계약

event는 비동기이고, 소비자가 나중에 다시 붙을 수 있으며, historical replay까지 등장한다. 그래서 API보다 더 보수적으로 설계하는 편이 낫다.

### additive event로 버틸 수 있는 경우

- 새 optional field 추가
- old consumer가 unknown field를 무시할 수 있음
- event 의미와 ordering key가 유지됨

### 새 event type 또는 `v2`가 필요한 경우

- event 이름은 같지만 의미가 달라짐
- required field가 추가되어 old consumer가 정상 처리할 수 없음
- partition key, ordering, idempotency key 기준이 달라짐
- payload shape보다 business meaning이 바뀜

### 실무 전략

| 전략 | 언제 쓰나 | 장점 | 주의점 |
| --- | --- | --- | --- |
| additive field | tolerant consumer가 가능 | 가장 비용이 낮다 | consumer contract 테스트 필요 |
| upcaster/downcaster | topic을 유지하고 중간 변환층을 둘 수 있음 | producer/consumer 이행이 부드럽다 | 변환층이 장기부채가 되기 쉽다 |
| 새 event type | 의미 자체가 바뀜 | semantic break를 명확히 드러낸다 | 한동안 두 흐름을 같이 운영해야 한다 |
| dual publish | migration bridge가 짧게 필요 | consumer 이행이 쉽다 | 반드시 임시 전략이어야 하며 outbox 기반이 안전하다 |

Kafka/Avro/Protobuf 같은 schema registry를 쓴다면 compatibility mode를 팀 규칙으로 먼저 정하는 편이 좋다. `BACKWARD`, `FORWARD`, `FULL_TRANSITIVE`는 단순 옵션이 아니라 "누구를 먼저 배포할 수 있는가"를 바꾼다.

## 7) Backfill, replay, rebuild를 구분해야 한다

이 셋을 섞으면 CD가 쉽게 꼬인다.

- backfill: 기존 source-of-truth row를 새 schema나 새 invariant에 맞게 채운다.
- replay: event log를 다시 읽어 파생 상태를 재생성한다.
- rebuild: projection, cache, search index처럼 파생 시스템을 통째로 다시 만든다.

### 무엇을 고를까

| 문제 | 더 자연스러운 선택 |
| --- | --- |
| 새 nullable column에 과거 값 채우기 | backfill |
| read model schema 교체 | rebuild 또는 replay |
| traffic이 지나가는 row만 천천히 바꿔도 됨 | lazy backfill |
| external webhook payload를 과거분까지 새 계약으로 다시 보내야 함 | 새 publisher/replay pipeline 검토 |

좋은 backfill/rebuild job은 공통으로 아래가 필요하다.

- idempotent
- resumable
- bounded transaction or bounded batch
- progress metrics
- validation query

validation 예시는 이 정도가 기본이다.

- `new_column IS NULL` row count
- old/new representation mismatch count
- consumer lag 또는 projection lag
- replay cursor 또는 checkpoint

## 8) CD를 지속가능하게 만드는 기본 순서

1. change를 DB/API/event/data 중 어디 문제인지 먼저 분해한다.
2. additive DB expand가 가능한지 본다.
3. API adapter 또는 event bridge로 old/new consumer를 함께 받게 만든다.
4. compatibility version을 배포한다.
5. backfill, replay, rebuild를 별도 운영 job으로 수행한다.
6. feature flag 또는 routing으로 새 경로를 cutover한다.
7. metrics와 mismatch count가 안정화되면 old contract를 deprecate한다.
8. 마지막에 contract migration 또는 old version removal을 한다.

여기서 중요한 것은 "cutover"와 "contract"를 분리하는 것이다.

- cutover는 새 경로를 기본값으로 바꾸는 시점이다.
- contract는 old path를 지우는 시점이다.

둘을 같은 배포에 넣으면 rollback이 훨씬 어려워진다.

## 9) 하지 않는 편이 좋은 것

- DB column rename이 보이자마자 API version부터 올린다.
- event payload 의미가 바뀌었는데 field만 조금 바꾼 것처럼 포장한다.
- dual publish를 영구 전략처럼 운영한다.
- 큰 backfill을 Alembic revision 안에서 한 번에 끝내려 한다.
- old consumer가 남아 있는데 contract migration을 실행한다.
- version을 올렸으니 observability와 deprecation policy는 덜 중요하다고 생각한다.

## 10) 팀 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>이 변화는 진짜 semantic break인가</h3>
    <p>표현 변화인지, 소비자 의미가 달라지는 변화인지 먼저 구분한다.</p>
  </div>
  <div class="check-card">
    <h3>version 없이 additive하게 풀 수 있는가</h3>
    <p>새 version은 마지막 수단으로 두는 편이 운영비가 낮다.</p>
  </div>
  <div class="check-card">
    <h3>boundary만 version-aware한가</h3>
    <p>service core 전체가 version 분기로 갈라지지 않게 한다.</p>
  </div>
  <div class="check-card">
    <h3>backfill 또는 replay가 필요한가</h3>
    <p>코드 배포만으로 historical state가 맞춰지지 않는다면 운영 job을 따로 잡는다.</p>
  </div>
  <div class="check-card">
    <h3>contract removal이 마지막 단계인가</h3>
    <p>cutover 이후 안정화와 관측 기간을 둔 뒤 old contract를 제거한다.</p>
  </div>
</div>

## 같이 읽으면 좋은 문서

1. [Alembic과 Zero-Downtime Migration](/sqlalchemy/alembic-and-zero-downtime)
2. [Progressive Delivery + Alembic](/playbooks/progressive-delivery-and-alembic)
3. [Idempotency와 Outbox](/playbooks/idempotency-and-outbox)
4. [Client Protocol과 Reconnect](/fastapi/websocket-client-protocol-and-reconnect)

## 공식 자료

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [SQLAlchemy naming conventions](https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions)
- [Confluent Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)
- [Stripe API versioning](https://docs.stripe.com/api/versioning)
- [Stripe webhook versioning](https://docs.stripe.com/webhooks/versioning)
- [Versions in Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/api-management-versions)
