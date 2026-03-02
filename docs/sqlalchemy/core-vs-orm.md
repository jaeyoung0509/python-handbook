# Core vs ORM

<p class="lead">SQLAlchemy 2.0을 깊게 이해하려면 "Core와 ORM 중 하나만 고르면 된다"는 식으로 보면 안 된다. ORM query도 결국 Core statement 위에서 움직이고, 실전에서는 Core의 표현력과 ORM의 객체 매핑을 상황에 따라 섞는 감각이 중요하다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: Core는 SQL expression과 실행 모델에 가깝고, ORM은 Python 객체와 unit of work에 가깝다. 둘은 대립 관계가 아니라 층위가 다르다. 읽기 전용 집계, 대량 작업, 정교한 SQL shape는 Core 쪽 감각이 중요하고, 엔티티 수명주기와 변경 추적은 ORM이 강하다.</p>
</div>

## 큰 그림

<MermaidDiagram
  caption="SQLAlchemy 2.0에서는 ORM도 `select()` 같은 statement 구성을 적극적으로 사용한다. Core는 아래층, ORM은 그 위에 올라간 매핑/상태 추적 층으로 이해하는 편이 좋다."
  chart="flowchart TB; A[Table metadata and SQL expressions] --> B[Core statement objects]; B --> C[Engine and Connection execution]; B --> D[ORM Session execution]; D --> E[Mapped entities and identity map];"
/>

## Core가 강한 영역

- 복잡한 join, CTE, window function
- bulk insert/update/delete
- 리포팅, 통계, 관리용 read path
- ORM entity가 필요 없는 projection query

## ORM이 강한 영역

- 엔티티 생성/변경 추적
- relationship와 aggregate 다루기
- unit of work와 flush/commit 관리
- 도메인 규칙이 엮인 write path

## SQLAlchemy 2.0 스타일의 핵심 변화

이제 ORM에서도 `Query` 체인보다 `select()` statement를 중심으로 읽는 감각이 중요하다.

```py
from sqlalchemy import select
from sqlalchemy.orm import Session


def list_active_users(session: Session) -> list[User]:
    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.created_at.desc())
    )
    return list(session.scalars(stmt))
```

<p class="code-caption">이 코드는 ORM 객체를 반환하지만, 질의 자체는 Core statement로 작성된다. SQLAlchemy 2.0은 바로 이 "statement first" 감각을 중심으로 읽는 편이 좋다.</p>

## Core projection을 섞는 읽기 모델

```py
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def count_users_by_role(session: Session) -> list[tuple[str, int]]:
    stmt = (
        select(User.role, func.count(User.id))
        .group_by(User.role)
        .order_by(User.role)
    )
    return [(role, count) for role, count in session.execute(stmt)]
```

- 이 경우 ORM entity를 굳이 만들 필요가 없다.
- admin/reporting endpoint는 projection query가 더 자연스러운 경우가 많다.
- read model과 write model을 같은 모양으로 통일하려는 강박이 오히려 복잡성을 키울 수 있다.

## 언제 Core를 더 앞세우면 좋은가

| 상황 | 추천 | 이유 |
| --- | --- | --- |
| 도메인 write path | ORM 중심 | 상태 추적과 flush가 자연스럽다 |
| 대시보드/리포트 | Core projection 중심 | entity hydration 비용이 불필요할 수 있다 |
| 대량 변경 | Core statement 또는 bulk 전략 | 객체 단위 추적 비용을 줄인다 |
| 복잡한 SQL 최적화 | Core 중심 | SQL shape를 더 직접적으로 제어할 수 있다 |

## 잘못 섞는 방식

- 모든 query 결과를 무조건 ORM entity로 만든다.
- 반대로 모든 코드를 row tuple 기반으로 밀어 ORM의 장점을 버린다.
- repository 하나에 read model, write model, ad-hoc reporting query를 전부 몰아넣는다.

## 설계 기준

- write path는 aggregate와 transaction 경계를 기준으로 ORM을 쓴다.
- read path는 API가 요구하는 shape를 기준으로 projection을 설계한다.
- Core를 쓴다고 Session을 버리는 것이 아니라, Session 안에서 `execute()`로 statement를 실행할 수 있다.

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>read와 write를 구분</h3>
    <p>엔티티 변경 추적이 필요한 write path와 projection 중심 read path를 같은 추상화에 억지로 맞추지 않는다.</p>
  </div>
  <div class="check-card">
    <h3>statement first</h3>
    <p>SQLAlchemy 2.0에서는 `select()`와 loader option을 읽는 감각이 ORM 이해의 출발점이다.</p>
  </div>
  <div class="check-card">
    <h3>entity hydration 비용 인식</h3>
    <p>반드시 객체가 필요한 경우에만 ORM entity를 만들고, 그렇지 않다면 더 얇은 projection을 고려한다.</p>
  </div>
  <div class="check-card">
    <h3>Session ownership 유지</h3>
    <p>Core query를 써도 transaction 소유권은 여전히 session/use-case 경계가 가져야 한다.</p>
  </div>
</div>

## 공식 자료

- [SQLAlchemy Unified Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [SQLAlchemy ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
- [SQLAlchemy Core Tutorial](https://docs.sqlalchemy.org/en/20/core/tutorial.html)
