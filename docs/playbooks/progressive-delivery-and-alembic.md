# Progressive Delivery + Alembic

<p class="lead">`blue-green`, `canary`, `rolling update`는 애플리케이션 트래픽을 점진적으로 바꾸는 전략이지, 데이터베이스를 둘로 쪼개 주는 전략이 아니다. 대부분의 서비스는 하나의 운영 DB를 공유하므로, progressive delivery를 하더라도 schema는 여전히 old app과 new app이 동시에 견딜 수 있어야 한다. 여기서 Alembic의 역할은 DDL 실행기가 아니라 rollout 단계 사이의 호환성을 관리하는 기준점이 되는 것이다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 공유 DB가 있는 서비스에서 CD의 핵심은 "트래픽을 어떻게 옮기느냐"보다 "old/new app이 같은 schema를 얼마나 오래 같이 버틸 수 있느냐"다. 안전한 기본형은 `expand migration -> compatibility app deploy -> resumable backfill -> progressive traffic shift -> feature flag cutover -> later contract migration`이다.</p>
</div>

<MermaidDiagram
  caption="배포 전략이 rolling이든 blue-green이든 canary든, shared DB를 쓰는 순간 schema 호환성 단계는 공통으로 필요하다."
  chart="flowchart LR; A[&quot;CI: revision review and upgrade test&quot;] --> B[&quot;CD: expand migration job&quot;]; B --> C[&quot;deploy compatibility version&quot;]; C --> D[&quot;run resumable backfill&quot;]; D --> E[&quot;progressive traffic shift&quot;]; E --> F[&quot;feature flag cutover&quot;]; F --> G[&quot;later contract migration&quot;];"
/>

## 1) 가장 먼저 인정해야 할 사실: DB는 대개 shared singleton이다

blue-green이나 canary를 도입하면 앱 버전은 둘 이상이 될 수 있지만, 운영 DB는 대개 하나다.

그래서 아래가 항상 더 중요하다.

- old app + expanded schema가 안전한가
- new app + expanded schema가 안전한가
- old app + contracted schema는 언제부터 불가능해지는가

배포 전략은 앱 트래픽 제어 방식이고, schema compatibility는 별도 문제다.

## 2) CI에서 Alembic을 어떻게 써야 하나

CI에서 가장 흔한 실수는 revision 파일 생성만 확인하고 끝내는 것이다. 실제로는 아래까지 봐야 한다.

### CI 기본 체크

1. `alembic revision --autogenerate` 결과를 사람 리뷰한다.
2. ephemeral DB에서 `alembic upgrade head`가 깨지지 않는지 본다.
3. 가능하면 현재 운영 `head`에서 새 `head`까지 upgrade 경로를 재현한다.
4. 업그레이드된 schema 위에서 앱 테스트를 돌린다.
5. destructive change인지, backfill이 필요한지, rollout 단계가 분리됐는지 확인한다.

### CI에서 묻는 질문

- rename인데 drop + add처럼 보이지 않는가
- autogenerate가 index/constraint 의도를 놓치지 않았는가
- contract 단계가 같은 릴리스에 섞여 있지 않은가
- backfill이 Alembic revision 안에 들어가도 되는 작은 작업인가

## 3) CD 기본형: migration job과 deploy job을 분리한다

실무 baseline은 아래 순서가 가장 안전하다.

### 단계 1. expand migration job

- nullable column 추가
- additive index / table / constraint 추가
- old app이 깨지지 않는 변화만 먼저 반영

### 단계 2. compatibility app deploy

- old/new column을 둘 다 이해하는 버전 배포
- `dual read`, `dual write`, feature flag off 상태 준비
- 아직 contract는 하지 않음

### 단계 3. backfill job

- 큰 data migration은 별도 job 또는 worker로 실행
- chunked transaction, checkpoint, retry, metrics 포함

### 단계 4. progressive traffic shift

- rolling update, blue-green, canary, Lambda alias 중 하나로 앱 트래픽 이동
- 이 시점에도 schema는 old/new 버전이 같이 버틸 수 있어야 함

### 단계 5. cutover

- feature flag 또는 config로 읽기/쓰기 기준을 새 column으로 전환
- metrics, error rate, lag를 확인

cutover는 단순 config flip이 아니라 승인 가능한 gate로 보는 편이 낫다.

- `new_column IS NULL`가 사실상 0인지
- old/new representation mismatch query가 허용 기준 이하인지
- app error rate, p95/p99 latency, downstream consumer lag가 안정적인지
- rollback 시 feature flag 또는 routing만으로 즉시 되돌릴 수 있는지

### 단계 6. later contract migration

- old app이 완전히 사라진 다음 old column / old constraint 제거
- 보통 다음 릴리스나 충분한 안정화 뒤에 수행

rollback 의미도 단계별로 다르다.

- cutover 이전 또는 직후의 rollback은 보통 app rollback, traffic shift 중단, feature flag off로 푸는 편이 맞다.
- contract 이후에는 "DB downgrade"보다 forward fix가 현실적인 경우가 많다.
- 그래서 contract 직전의 관측 기간이 실제 rollback 가능성을 지키는 마지막 구간이 된다.

## 4) GitHub Actions에서 gate를 어떻게 두면 좋은가

shared DB 서비스라면 `app deploy`와 `db change`를 같은 하나의 무승인 job으로 뭉치지 않는 편이 좋다.

GitHub Actions의 environment를 아래처럼 분리해 두면 운영자가 승인 포인트를 나누기 쉽다.

```yaml
name: deploy

on:
  push:
    branches: [main]

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run pytest
      - run: uv run ruff check .
      - run: uv run ty check

  migrate-expand:
    needs: test-and-build
    runs-on: ubuntu-latest
    environment: production-db
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run alembic upgrade head

  deploy-compatible:
    needs: migrate-expand
    runs-on: ubuntu-latest
    environment: production-app
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy-compatible.sh

  backfill:
    needs: deploy-compatible
    runs-on: ubuntu-latest
    environment: production-db
    steps:
      - uses: actions/checkout@v4
      - run: uv sync --dev
      - run: uv run python -m app.jobs.backfill_display_name --batch-size 1000

  promote-traffic:
    needs: backfill
    runs-on: ubuntu-latest
    environment: production-app
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/promote-traffic.sh
```

<p class="code-caption">포인트는 `production-db`와 `production-app` 환경을 분리하는 것이다. DB 승인과 앱 승인 타이밍이 같지 않을 수 있고, backfill도 별도 보호 구간으로 두는 편이 안전하다.</p>

## 5) backfill은 Alembic revision 안에 언제 넣고 언제 빼야 하나

| 경우 | Alembic revision 안에 가능 | 별도 backfill job 권장 |
| --- | --- | --- |
| row 수가 작고 수 초 안에 끝남 | 예 | 가능하지만 굳이 분리 안 해도 됨 |
| 긴 업데이트, batch 필요, resume 필요 | 아니오 | 예 |
| lock 영향이 크고 throttle 필요 | 아니오 | 예 |
| 운영 중 지표 보며 천천히 돌려야 함 | 아니오 | 예 |

즉, "DDL과 함께 넣을 수 있는 작은 data fix"와 "운영 migration job"을 분리해야 한다.

## 6) 좋은 backfill job의 조건

### 1. idempotent

이미 채운 row를 다시 처리해도 문제없어야 한다.

```sql
UPDATE users
SET display_name = full_name
WHERE display_name IS NULL
  AND id BETWEEN :start_id AND :end_id
```

### 2. resumable

- checkpoint table 또는 cursor를 둔다.
- `last_processed_id`, `updated_rows`, `updated_at` 같은 상태를 저장한다.

### 3. bounded transaction

- 한 번에 수백만 row를 한 transaction으로 묶지 않는다.
- 작은 batch마다 commit한다.

### 4. observable

- rows/sec
- lag
- remaining null count
- error count
- last cursor

### 5. throttled

- replica lag, lock, DB CPU를 보며 batch size나 sleep을 조절할 수 있어야 한다.

### cutover gate와 contract gate는 다르다

운영에서 자주 생기는 실수는 traffic promotion과 contract migration을 같은 승인 단위로 묶는 것이다.

- cutover gate에서는 backfill 완료율, mismatch query 결과, error budget 소모, read/write path 전환 여부를 본다.
- contract gate에서는 old pod, old worker, old cron, old client traffic이 실제로 사라졌는지 본다.
- shared DB에서는 "트래픽이 새 버전으로 갔다"와 "old contract를 지워도 된다"가 같은 뜻이 아니다.

## 7) Python backfill worker 기본형

```py
def run_backfill(session_factory: SessionFactory, batch_size: int = 1000) -> None:
    cursor = load_checkpoint("users_display_name")

    while True:
        with session_factory() as session:
            rows = session.execute(
                select(User.id, User.full_name)
                .where(User.id > cursor, User.display_name.is_(None))
                .order_by(User.id)
                .limit(batch_size)
            ).all()

            if not rows:
                return

            for user_id, full_name in rows:
                session.execute(
                    update(User)
                    .where(User.id == user_id, User.display_name.is_(None))
                    .values(display_name=full_name)
                )

            cursor = rows[-1][0]
            save_checkpoint(session, "users_display_name", cursor)
            session.commit()
```

이 패턴은 keyset cursor, 작은 transaction, checkpoint 저장을 한 번에 보여준다.

## 8) rolling update에서의 규칙

Kubernetes `Deployment`의 `RollingUpdate`는 old/new ReplicaSet이 한동안 같이 살아 있다.

그래서 규칙은 단순하다.

- expand migration 먼저
- new app은 dual read/write 가능해야 함
- contract migration은 old pod가 완전히 사라진 뒤

rolling update는 가장 단순하지만, N-1 / N compatibility 요구가 가장 직접적으로 드러난다.

## 9) blue-green에서의 규칙

blue-green은 preview stack을 따로 둘 수 있어 검증은 좋지만, DB가 분리되는 것은 아니다.

### 안전한 순서

1. expand migration
2. green 배포
3. preview smoke / analysis
4. 필요하면 backfill 실행
5. traffic switch
6. blue 유지하면서 post-promotion 검증
7. 안정화 후 blue 제거
8. contract는 나중 릴리스

### 핵심 오해

blue-green이라고 해서 `blue DB`와 `green DB`가 자동으로 생기지 않는다. shared DB라면 schema는 여전히 backward compatible해야 한다.

## 10) canary에서의 규칙

canary는 blast radius를 줄이는 데 좋지만, schema migration을 canary로 안전하게 만들지는 못한다.

### 왜 그런가

- canary 1%라도 shared DB에 write를 한다.
- stable 99%와 canary 1%가 같은 row와 table을 본다.
- 즉, destructive schema change는 여전히 위험하다.

### canary에 잘 맞는 것

- app behavior 분석
- query cost / error rate / latency 분석
- feature flag on/off 검증

### canary에 안 맞는 것

- old code가 못 읽는 contract migration
- lock-heavy rewrite
- "1%니까 괜찮겠지"라고 생각하는 destructive DDL

## 11) Lambda weighted alias / CodeDeploy canary도 본질은 같다

AWS Lambda weighted alias나 CodeDeploy canary/linear도 앱 버전 트래픽만 나눌 뿐, DB schema 호환성 문제를 해결하지는 않는다.

추가로 Lambda 쪽은 아래를 기억해야 한다.

- alias는 최대 두 버전만 가리킨다.
- low traffic에서는 configured weight와 실제 비율 편차가 커질 수 있다.
- weighted alias는 canary에 좋지만 backfill/DDL 분리를 대신하지 않는다.

즉, Lambda도 `expand -> compatible code -> backfill -> traffic shift -> contract later` 순서는 같다.

## 12) 전략별 비교 표

| 전략 | 장점 | schema 관점 핵심 규칙 | 흔한 실수 |
| --- | --- | --- | --- |
| rolling update | 가장 단순, 기본 기능으로 가능 | old/new pod 동시 호환 필수 | contract를 같은 릴리스에 넣음 |
| blue-green | preview stack 검증이 좋음 | DB는 shared라 backward compatible 필수 | green 검증 후 바로 contract |
| canary | blast radius 제어, metrics 기반 promotion | schema는 canary로 안전해지지 않음 | destructive migration도 1%면 괜찮다고 생각 |
| Lambda alias / CodeDeploy | 서버리스 트래픽 점진 이동 | DB 호환성 규칙은 동일 | weighted traffic만 보고 DB migration을 같이 섞음 |

## 13) 하지 않는 편이 좋은 것

- app startup에서 Alembic migration을 자동 실행한다.
- 큰 backfill을 Alembic revision 안에서 한 transaction으로 끝내려 한다.
- blue-green이면 schema 호환성을 덜 봐도 된다고 생각한다.
- canary 비율이 낮으니 destructive migration도 괜찮다고 본다.
- contract migration을 traffic shift 직후 즉시 실행한다.

## 운영 시나리오로 점검하기

| symptom | 먼저 볼 것 | likely root cause | safe mitigation | what not to do |
| --- | --- | --- | --- | --- |
| canary 10%까지는 괜찮았는데 50%부터 old worker가 터진다 | old/new app이 같은 expanded schema를 모두 이해하는지 본다 | compatibility deploy 없이 사실상 contract behavior를 먼저 켰다 | feature flag를 되돌리고 compatibility path를 복구한 뒤 다시 promotion한다 | "canary니까 blast radius가 작다"며 destructive path를 유지한다 |
| backfill 중 replica lag와 DB CPU가 급등한다 | batch size, checkpoint, lock pattern, throttle 유무를 본다 | backfill이 resumable/throttled job이 아니라 사실상 대형 migration으로 실행됐다 | batch를 줄이고 throttle을 넣고, 필요하면 traffic shift를 멈춘다 | Alembic downgrade로 한 번에 되돌리려 한다 |
| promotion 직후 rollback 요구가 들어왔는데 contract가 이미 실행됐다 | contract migration 시점과 old consumer 존재 여부를 본다 | cutover gate와 contract gate를 같은 승인 단위로 묶었다 | DB downgrade보다 forward fix 또는 feature compatibility 복구를 우선 검토한다 | shared DB에서 즉시 schema downgrade가 항상 가능하다고 가정한다 |

## Code Review Lens

- expand, compatibility deploy, backfill, cutover, contract가 분리된 단계로 읽히는지 본다.
- Alembic revision과 operational backfill job의 책임이 분리돼 있는지 본다.
- old/new app이 shared DB를 얼마나 오래 같이 견뎌야 하는지 명시돼 있는지 본다.
- rollback이 "앱 rollback"인지 "schema downgrade"인지 단계별로 다르게 정의되는지 본다.

## Common Anti-Patterns

- app startup 시 Alembic을 자동 실행해 rollout과 schema change를 강제로 결합한다.
- 큰 backfill을 revision 안에 넣고 한 transaction으로 끝내려 한다.
- canary나 blue-green이면 destructive migration도 괜찮다고 오해한다.
- traffic promotion과 contract migration을 같은 승인 버튼으로 묶는다.

## Likely Discussion Questions

- 왜 progressive delivery가 schema compatibility 문제를 자동으로 해결해 주지 않는가?
- 어떤 data change까지는 Alembic revision 안에 두고, 어떤 것은 별도 job으로 빼야 하는가?
- cutover gate와 contract gate를 왜 따로 봐야 하는가?
- rollback 전략이 stage마다 달라지는 이유는 무엇인가?

## Strong Answer Frame

- 먼저 shared DB에서는 rollout 전략과 schema 호환성이 다른 문제라고 분리해서 말한다.
- 그 다음 `expand -> compatible -> backfill -> cutover -> contract`의 순서를 기준선으로 둔다.
- Alembic revision, backfill worker, feature flag, traffic promotion의 역할을 나눠 설명한다.
- 마지막으로 rollback은 stage별로 의미가 다르며, contract 이후에는 forward fix가 더 현실적일 수 있다고 닫는다.

## 같이 읽으면 좋은 문서

1. [Alembic과 Zero-Downtime Migration](/sqlalchemy/alembic-and-zero-downtime)
2. [Lambda vs Kubernetes](/playbooks/lambda-vs-kubernetes)
3. [계약 진화와 지속가능한 CD](/playbooks/contract-evolution-and-sustainable-cd)
4. [배포별 Engine 설정](/sqlalchemy/deployment-and-engine-settings)

실행 감각은 `examples/progressive_delivery_backfill_lab.py`를 같이 보면 좋다.

## 공식 자료

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [Deployments | Kubernetes](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Argo Rollouts Canary](https://argo-rollouts.readthedocs.io/en/stable/features/canary/)
- [Argo Rollouts BlueGreen](https://argo-rollouts.readthedocs.io/en/latest/features/bluegreen/)
- [AWS Lambda weighted alias routing](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)
