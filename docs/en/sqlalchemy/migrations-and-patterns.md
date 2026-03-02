# Migrations and Patterns

<p class="lead">SQLAlchemy 2.0 is not just a syntax refresh. It rewards a different day-to-day style: statement-centric querying, explicit transactions, typed declarative mappings, and short-lived sessions. Old 1.x habits often carry hidden complexity into new codebases.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: migration to 2.0 should be treated as a boundary cleanup, not only as a search-and-replace exercise. Move toward `select()`-centric code, explicit transaction ownership, typed models, and tighter session lifecycles.</p>
</div>

## The Shift from 1.x to 2.0

| Older habit | 2.0 mindset |
| --- | --- |
| `session.query(User)` everywhere | `select(User)` as the default query style |
| long-lived sessions | request- or use-case-scoped sessions |
| commit logic spread across helpers | commit owned by service or use-case boundaries |
| ORM entities crossing every boundary | explicit DTO and entity separation |
| type hints as decoration | `Mapped[...]` and `mapped_column()` as first-class mapping style |

## A Basic 2.0-Style Example

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

## How Far Should the Repository Pattern Go?

Repositories are useful, but trying to hide all of SQLAlchemy behind generic CRUD interfaces often makes things worse.

### When repositories help

- when a use case should express intent in domain language
- when you want query responsibility to stay out of routes and services
- when write models and read models should remain separate

### When repositories become counterproductive

- generic CRUD repositories with almost no business meaning
- attempts to hide pagination, projection, and loader differences completely
- interfaces that leak ORM details back out through dynamic filter kwargs

## Alembic Discipline Is Part of Modeling Discipline

- migrations are deployable change units, not passive byproducts
- autogenerate is a starting point, not a final answer
- naming conventions improve diff quality and operational safety
- destructive migrations may require multi-step rollout plans

## A Realistic Pattern: Service Owns the Transaction

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

The important design point is that repositories perform persistence work, but transaction completion belongs to the service or use-case boundary. That keeps multi-step changes atomic.

## Migration Checklist

<div class="doc-checklist">
  <div class="check-card">
    <h3>Normalize on `select()`</h3>
    <p>Write new code in statement-centric style and retire old `Query` chains gradually.</p>
  </div>
  <div class="check-card">
    <h3>Rescope sessions</h3>
    <p>Eliminate long-lived sessions, hidden commits, and helper-created session objects first.</p>
  </div>
  <div class="check-card">
    <h3>Review Alembic output</h3>
    <p>Check constraints, indexes, and data-migration needs instead of trusting autogenerate blindly.</p>
  </div>
  <div class="check-card">
    <h3>Avoid over-generic repositories</h3>
    <p>Prefer explicit use-case queries over one giant CRUD abstraction that hides important SQL differences.</p>
  </div>
</div>

## Official References

- [SQLAlchemy 2.0 Major Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [SQLAlchemy ORM Mapped Class Configuration](https://docs.sqlalchemy.org/en/20/orm/mapper_config.html)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
