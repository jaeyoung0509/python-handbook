# Migrations and Patterns

<p class="lead">SQLAlchemy 2.0은 단순 문법 교체 버전이 아니다. `Query` 중심 습관, autocommit 감각, 느슨한 session 사용, ORM entity를 API에 바로 노출하는 패턴이 누적된 코드베이스에서는 2.0 스타일로 사고방식을 바꾸는 것이 더 중요하다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: 2.0에서는 `select()` 중심 statement style, 명시적 transaction, typed declarative mapping, 짧은 session scope가 기본이다. migration은 "구문 변환"이 아니라 코드 경계를 다시 정리하는 기회로 보는 편이 좋다.</p>
</div>

## 1.x 감각과 2.0 감각의 차이

| 이전 습관 | 2.0 기준 감각 |
| --- | --- |
| `session.query(User)` 중심 | `select(User)` 중심 |
| session을 오래 유지 | 요청 또는 use case 범위로 짧게 유지 |
| commit 위치가 여기저기 흩어짐 | service/use-case 경계에서 commit 통제 |
| ORM entity를 어디든 전달 | DTO와 entity 경계를 명시 |
| 선언형 모델에 타입 힌트가 부가물 | `Mapped[...]`, `mapped_column()`이 기본 |

## 2.0 스타일 기본 예제

```py
from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]


def get_user_by_email(session: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return session.scalar(stmt)
```

## repository pattern은 어디까지 쓰면 좋은가

repository는 유용하지만, 모든 SQLAlchemy 기능을 repository 인터페이스 뒤에 숨기려는 순간 오히려 나빠질 수 있다.

### 도움이 되는 경우

- 도메인 use case가 "무엇을 원하나"를 표현하고 싶을 때
- 테스트에서 fake repository보다 test DB를 쓰더라도 질의 책임을 정리하고 싶을 때
- write model과 read model을 분리해 API 계층을 깔끔하게 유지하고 싶을 때

### 과해지는 경우

- CRUD 메서드만 잔뜩 만든 generic repository
- loader option, pagination, projection 차이를 전부 숨기려는 시도
- 결국 `filter_by_kwargs` 같은 ORM 누수 인터페이스가 생김

## Alembic discipline은 모델링 discipline과 연결된다

- migration은 모델 파일 저장의 부산물이 아니라 배포 가능한 변경 단위다.
- autogenerate는 시작점이지, 최종 검토 없는 정답이 아니다.
- naming convention을 초기에 잡아두면 diff 품질과 운영 안정성이 좋아진다.
- destructive migration은 코드 배포와 분리된 단계적 롤아웃이 필요할 수 있다.

## 실전 패턴: service가 transaction을 소유한다

```py
from sqlalchemy.orm import Session


class UserService:
    def __init__(self, session: Session, users: UserRepository) -> None:
        self.session = session
        self.users = users

    def rename(self, user_id: int, new_name: str) -> UserRead:
        with self.session.begin():
            user = self.users.require(user_id)
            user.name = new_name
            self.session.flush()
            return UserRead(id=user.id, name=user.name, email=user.email)
```

이 패턴의 핵심은 repository가 DB 접근을 담당하고, transaction completion은 service가 소유한다는 점이다. 그래야 한 use case 안 여러 변경 작업을 원자적으로 묶을 수 있다.

## migration 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>`select()` 스타일 정착</h3>
    <p>새 코드는 모두 statement-centric style로 작성하고, 오래된 `Query` 체인은 점진적으로 정리한다.</p>
  </div>
  <div class="check-card">
    <h3>session scope 재정리</h3>
    <p>긴 세션, 숨은 commit, 헬퍼 내부 session 생성 패턴을 먼저 제거한다.</p>
  </div>
  <div class="check-card">
    <h3>Alembic 검토 습관</h3>
    <p>autogenerate 결과를 그대로 믿지 말고 constraint, index, data migration 필요성을 직접 검토한다.</p>
  </div>
  <div class="check-card">
    <h3>generic repository 남용 금지</h3>
    <p>모든 query shape를 하나의 CRUD 인터페이스에 욱여넣기보다, use-case 중심 query 메서드를 명시적으로 두는 편이 낫다.</p>
  </div>
</div>

## 공식 자료

- [SQLAlchemy 2.0 Major Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [SQLAlchemy ORM Mapped Class Configuration](https://docs.sqlalchemy.org/en/20/orm/mapper_config.html)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
