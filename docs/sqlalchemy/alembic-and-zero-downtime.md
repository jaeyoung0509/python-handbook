# Alembic과 Zero-Downtime Migration

<p class="lead">SQLAlchemy를 잘 써도 migration discipline이 약하면 운영에서 바로 무너진다. Alembic의 핵심은 "모델을 바꿨으니 자동 생성한다"가 아니라, 배포 가능한 schema 변경 단위를 revision graph로 관리하는 것이다. 특히 실서비스에서는 expand, dual write, backfill, cutover, contract를 분리해서 생각해야 한다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Alembic은 모델 스냅샷 도구가 아니라 schema history를 관리하는 도구다. autogenerate는 출발점일 뿐이고, zero-downtime migration은 additive change부터 배포한 뒤 앱과 DB를 단계적으로 같이 움직이는 운영 discipline이다.</p>
</div>

<MermaidDiagram
  caption="실무 migration은 'DDL 한 번 실행'보다 단계적 rollout에 가깝다."
  chart="flowchart LR; A[&quot;expand schema&quot;] --> B[&quot;deploy app with dual read or dual write&quot;]; B --> C[&quot;backfill old rows&quot;]; C --> D[&quot;switch reads and writes&quot;]; D --> E[&quot;contract old column or constraint&quot;];"
/>

## 1) Alembic을 어떤 도구로 봐야 하나

Alembic은 현재 모델 정의를 DB에 맞추는 "상태 동기화 버튼"이 아니다.

더 정확한 mental model은 이렇다.

- revision은 배포 가능한 변경 단위다.
- revision끼리는 graph를 이룬다.
- 운영 DB는 어느 revision까지 적용되었는지 상태를 가진다.
- 앱 버전과 schema 버전은 항상 1:1로 같이 움직이지 않는다.

즉, migration은 코드 배포와 분리된 별도 운영 객체다.

## 2) revision graph와 branch를 이해해야 한다

기본적인 Alembic revision은 `down_revision`으로 이전 노드를 가리킨다.

```py
revision = "20260306_add_display_name"
down_revision = "20260215_initial_users"
branch_labels = None
depends_on = None
```

여기서 중요한 건 "최신 head 하나만 있으면 된다"가 아니라, branch가 생겼을 때 merge revision이 왜 필요한지 이해하는 것이다.

### branch가 생기는 상황

- 여러 기능 브랜치가 같은 시기에 migration을 추가했다.
- 한 팀은 index를 추가했고 다른 팀은 column을 추가했다.
- 둘 다 main에 합쳐지면서 head가 둘이 된다.

이때 revision graph를 merge하지 않고 방치하면 환경마다 적용 순서가 달라질 수 있다.

## 3) autogenerate는 작성 보조지, 승인 버튼이 아니다

autogenerate가 잘 도와주는 것:

- table / column 추가
- 기본적인 constraint 변화 감지
- metadata와 DB 차이의 1차 스캐닝

autogenerate가 대신 못 해주는 것:

- data migration 전략
- 긴 backfill 작업 계획
- lock 영향 판단
- destructive change rollout
- rename 의도와 drop + add를 구분하는 판단

즉, `alembic revision --autogenerate`는 시작점이지 끝이 아니다.

특히 rename은 가장 흔한 함정이다.

- Alembic은 보통 "이 column이 이름만 바뀌었다"는 의도를 자동으로 모른다.
- 그래서 `full_name -> display_name` 같은 변경이 `drop_column + add_column`처럼 보일 수 있다.
- 운영에서는 이 차이가 치명적이다. rename 의도라면 expand/dual read/backfill/contract로 쪼개야지, autogenerate 결과를 그대로 실행하면 안 된다.

## 4) naming convention을 먼저 잡아야 하는 이유

constraint 이름을 DB가 자동 생성하게 두면 migration diff와 운영 rollback이 읽기 어려워진다.

```py
from sqlalchemy import MetaData


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
```

이 규칙이 있으면 Alembic diff가 더 안정적이고, 인덱스/constraint를 운영에서 추적하기 쉬워진다.

## 5) zero-downtime migration의 기본 패턴: expand -> migrate data -> contract

예를 들어 `full_name`을 `display_name`으로 바꾸고 싶다고 하자.

### 나쁜 접근

1. 기존 column drop
2. 새 column add
3. 앱 코드도 동시에 교체

이 접근은 old app / new app / old schema / new schema 조합 중 하나라도 어긋나면 바로 장애로 이어진다.

### 더 안전한 접근

1. 새 column을 nullable하게 추가한다. `expand`
2. 앱이 old/new column을 모두 이해하게 배포한다. `dual read` 또는 `dual write`
3. 오래된 row를 backfill한다.
4. 충분히 안정화되면 읽기/쓰기를 새 column 기준으로 전환한다.
5. 마지막에 old column을 제거한다. `contract`

## 6) rollout compatibility 표를 항상 본다

| 앱 버전 | 스키마 상태 | 안전한가 | 이유 |
| --- | --- | --- | --- |
| old app | old schema | 예 | 기존 조합 |
| old app | expanded schema | 예 | additive change는 대체로 안전 |
| new app | expanded schema | 예 | dual read/write 전략이면 안전 |
| new app | contracted schema | 예 | cutover 뒤라면 가능 |
| old app | contracted schema | 아니오 | old code가 이미 제거된 column을 기대할 수 있음 |

즉, contract는 항상 맨 마지막이다.

## 7) data migration은 schema migration과 다른 성격이다

`ALTER TABLE` 몇 줄과 backfill 수백만 건 업데이트는 위험도가 다르다.

### data migration을 따로 보는 이유

- 오래 걸린다.
- lock을 오래 잡을 수 있다.
- dead tuple, WAL, replication lag 같은 운영 비용이 커진다.
- 중간 재시작, 배치 분할, progress 관찰이 필요할 수 있다.

많은 팀이 schema migration revision 안에 무거운 data migration을 한 번에 넣는데, 운영 리스크가 커진다. 경우에 따라서는 별도 batch job 또는 one-off worker로 분리하는 편이 낫다.

또 하나 놓치기 쉬운 점은 lock 특성이 DB engine마다 다르다는 것이다.

- PostgreSQL은 작업 종류에 따라 table rewrite나 강한 lock이 걸릴 수 있다. 예를 들어 일부 `ALTER TABLE`은 `ACCESS EXCLUSIVE` lock을 유발하고, index 생성도 `CONCURRENTLY` 같은 별도 전략이 필요할 수 있다.
- MySQL/InnoDB도 버전과 연산 종류에 따라 `INSTANT`, `INPLACE`, table copy 여부가 달라진다. "online DDL"이 항상 무중단을 뜻하지는 않는다.
- SQLite는 많은 schema 변경이 table rebuild 성격이라, 로컬 개발에서는 편해도 운영 zero-downtime 리허설 환경으로는 대표성이 약하다.

즉, migration 위험 평가는 ORM이 아니라 실제 운영 엔진 기준으로 해야 한다.

## 8) 앱 startup에서 migration을 자동 실행하지 않는 편이 좋은 이유

개발 환경에서는 편해 보여도 운영에서는 문제가 된다.

- multi-worker 배포에서 동시에 migration을 치려 할 수 있다.
- startup latency가 예측 불가능해진다.
- 실패 시 app health와 schema state가 같이 꼬인다.
- Lambda처럼 cold start 경로에 migration이 섞이면 더 안 좋다.

권장 기준:

- migration은 CI/CD step 또는 운영 job으로 분리한다.
- app는 "이미 맞는 schema가 존재한다"는 전제에서 뜨게 한다.

## 9) Alembic 운영 체크리스트

### revision 작성 전

- additive change로 쪼갤 수 있는가
- rename인지 drop + add인지 명확한가
- constraint / index 이름이 안정적인가
- backfill이 필요한가

### revision 리뷰 시

- autogenerate 결과를 그대로 믿지 않았는가
- destructive change가 rollout 단계로 쪼개졌는가
- downgrade가 정말 현실적인가, 아니면 app rollback / forward fix가 더 맞는가
- 장시간 lock 가능성을 검토했는가

### 배포 전

- old app / new schema 조합이 안전한가
- new app / old schema 조합이 잠시라도 생길 수 있는가
- readiness / drain / worker restart 순서와 충돌하지 않는가

운영 rollback도 `downgrade()` 함수와 같은 뜻이 아니다.

- destructive migration 뒤에는 원래 데이터를 정확히 복원할 수 없을 수 있다.
- backfill이 이미 새 invariant를 만들어 버리면, schema만 내린다고 원상복구가 되지 않는다.
- 그래서 실제 rollback은 app rollback, feature flag off, forward fix에 더 자주 의존한다.

## 10) SQLAlchemy model 설계와 Alembic은 연결된다

- implicit naming이 많을수록 migration diff가 불안정하다.
- domain 개념과 DB rename를 한 번에 묶으면 rollout이 어려워진다.
- session/UoW 경계가 명확할수록 dual write 위치를 잡기 쉽다.

즉, migration discipline은 모델링 discipline의 연장이다.

## 11) 진짜 어려운 곳은 CI/CD와 progressive delivery다

실서비스에서는 Alembic revision을 잘 쓰는 것만으로 끝나지 않는다.

- migration job과 app deploy job을 분리해야 한다.
- 큰 backfill은 resumable job으로 따로 굴리는 편이 안전하다.
- rolling, blue-green, canary 모두 shared DB라면 schema compatibility 규칙을 피할 수 없다.

이 운영 축은 [Progressive Delivery + Alembic](/playbooks/progressive-delivery-and-alembic)에서 더 깊게 다루고, DB schema를 넘어 API/event/backfill까지 묶는 관점은 [계약 진화와 지속가능한 CD](/playbooks/contract-evolution-and-sustainable-cd)에서 이어서 정리한다.

## 이 저장소에서 같이 볼 문서

1. [Session과 Unit of Work](/sqlalchemy/session-and-unit-of-work)
2. [배포별 Engine 설정](/sqlalchemy/deployment-and-engine-settings)
3. [Lambda vs Kubernetes](/playbooks/lambda-vs-kubernetes)
4. [Progressive Delivery + Alembic](/playbooks/progressive-delivery-and-alembic)
5. [계약 진화와 지속가능한 CD](/playbooks/contract-evolution-and-sustainable-cd)

실행 감각은 `examples/alembic_zero_downtime_lab.py`, `examples/progressive_delivery_backfill_lab.py`를 같이 보면 좋다.

## 공식 자료

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- [SQLAlchemy naming conventions](https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions)
