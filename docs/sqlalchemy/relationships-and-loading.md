# Relationships and Loading

<p class="lead">SQLAlchemy 성능 문제의 상당수는 relationship 선언 자체보다 "언제 어떤 방식으로 로드되는가"에서 나온다. API 응답을 만들 때 lazy load가 숨어서 발생하면 N+1이 생기고, 반대로 무작정 joined load를 남발하면 row 폭발과 중복 데이터로 더 느려질 수 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: loading strategy는 모델 선언의 부가 옵션이 아니라 query 설계의 일부다. route가 원하는 응답 shape를 먼저 정하고, 그 shape에 맞는 loader option을 query 시점에 명시하는 편이 가장 안전하다.</p>
</div>

## 로딩 전략 큰 그림

<MermaidDiagram
  caption="관계 로딩은 '객체를 편하게 가져오는 옵션'이 아니라 SQL 수와 row shape를 바꾸는 결정이다."
  chart="flowchart LR; A[Select parent rows] --> B{Loader strategy}; B --> C[lazy: extra query on access]; B --> D[joinedload: join in same query]; B --> E[selectinload: secondary IN query]; B --> F[subqueryload: secondary subquery];"
/>

## 대표 전략을 이렇게 구분한다

| 전략 | 장점 | 위험 | 잘 맞는 경우 |
| --- | --- | --- | --- |
| `lazy` | 기본값, 필요할 때만 조회 | N+1, 숨은 I/O | 관계를 거의 안 읽는 내부 로직 |
| `joinedload()` | 한 번의 query로 관계 포함 | row 중복, 넓은 join | 단건 상세 조회, 작은 컬렉션 |
| `selectinload()` | 컬렉션 로딩에서 비교적 안정적 | 추가 query는 필요 | API 목록 응답, 중간 크기 컬렉션 |
| `subqueryload()` | 특정 상황에서 유용 | 요즘은 `selectinload()`가 더 단순한 경우 많음 | 레거시/특수 shape |

## 목록 API에서 가장 자주 쓰는 패턴

```py
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


def list_orders(session: Session) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(50)
    )
    return list(session.scalars(stmt))
```

<p class="code-caption">주문 목록에서 각 주문의 `items`를 같이 보여줘야 한다면, 컬렉션 관계에는 `selectinload()`가 기본 선택이 되는 경우가 많다. 부모 row 폭발 없이 후속 query로 필요한 관계를 묶어서 읽을 수 있기 때문이다.</p>

## 단건 상세 조회에서는 `joinedload()`가 자연스러울 수 있다

```py
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload


def get_order_detail(session: Session, order_id: int) -> Order | None:
    stmt = (
        select(Order)
        .options(joinedload(Order.customer))
        .where(Order.id == order_id)
    )
    return session.scalar(stmt)
```

- many-to-one 또는 one-to-one에 가깝고 row 폭발 위험이 작을 때 유리하다.
- 반대로 큰 one-to-many 컬렉션을 `joinedload()`로 붙이면 중복 row가 과도하게 커질 수 있다.

## API 경계와 로딩 전략은 같이 설계해야 한다

- 응답 DTO가 어떤 관계 필드를 포함하는지 먼저 결정한다.
- 그 뒤 query layer에서 필요한 loader option을 붙인다.
- serializer가 ORM 객체를 건드리면서 "나중에" 관계를 불러오게 두면 숨은 I/O가 생긴다.
- async 코드에서는 이런 lazy load가 특히 위험하다.

## `lazy="raise"`는 설계 문제를 빨리 드러낸다

```py
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    items: Mapped[list["OrderItem"]] = relationship(lazy="raise")
```

`lazy="raise"`는 관계가 미리 로드되지 않았는데 접근하면 예외를 내어, 숨은 lazy load를 조기에 잡는 데 도움이 된다. 특히 API serialization 경계에서 유용하다.

## cascade는 "편의 기능"이 아니라 도메인 규칙

- `delete-orphan`은 부모-자식 소유 관계가 정말 강할 때만 쓴다.
- cascade 설정은 aggregate 경계와 연결해서 읽어야 한다.
- 관계를 쉽게 지운다고 cascade를 넓게 열어두면 예상치 못한 삭제가 발생할 수 있다.

## 흔한 실수

- 목록 API에서 관계를 lazy load로 열어둔다.
- 모든 관계를 기본 eager load로 설정한다.
- serializer가 ORM entity를 돌아다니며 무엇을 읽는지 모른다.
- relationship cascade를 비즈니스 의미 없이 켠다.

## 실전 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>response shape 먼저</h3>
    <p>어떤 관계가 응답에 필요한지부터 정하고, 그 뒤에 query와 loader option을 설계한다.</p>
  </div>
  <div class="check-card">
    <h3>컬렉션은 `selectinload()` 우선 검토</h3>
    <p>목록 API의 one-to-many 컬렉션은 `selectinload()`가 가장 균형 잡힌 출발점인 경우가 많다.</p>
  </div>
  <div class="check-card">
    <h3>상세 단건은 `joinedload()` 가능</h3>
    <p>many-to-one 또는 작은 관계를 한 번에 가져와야 하면 `joinedload()`가 자연스럽다.</p>
  </div>
  <div class="check-card">
    <h3>숨은 lazy load를 조기에 터뜨리기</h3>
    <p>`lazy="raise"` 같은 방식을 써서 serializer나 template가 몰래 SQL을 날리는 상황을 빨리 발견한다.</p>
  </div>
</div>

## 공식 자료

- [SQLAlchemy Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [SQLAlchemy Basic Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
