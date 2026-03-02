# SQLAlchemy loading strategies: lazy loading, selectinload, and joinedload.
# SQLAlchemy 로딩 전략: lazy loading, selectinload, joinedload.
# Why: many SQLAlchemy performance bugs come from hidden N+1 queries or row explosion.
# 왜: SQLAlchemy 성능 문제는 숨은 N+1 쿼리나 row explosion에서 자주 나온다.
# Use when: learning which loading strategy fits list endpoints, detail views, and serializer boundaries.
# 언제 쓰나: 목록 API, 상세 조회, serializer 경계에 어떤 로딩 전략이 맞는지 익힐 때 좋다.

from __future__ import annotations

from sqlalchemy import ForeignKey, String, create_engine, event, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
    selectinload,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    members: Mapped[list["Member"]] = relationship(back_populates="team")


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team: Mapped[Team] = relationship(back_populates="members")


class QueryCounter:
    def __init__(self) -> None:
        self.count = 0

    def reset(self) -> None:
        self.count = 0


engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionFactory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
counter = QueryCounter()


@event.listens_for(engine, "before_cursor_execute")
def count_queries(
    _connection: object,
    _cursor: object,
    _statement: str,
    _parameters: object,
    _context: object,
    _executemany: bool,
) -> None:
    counter.count += 1


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionFactory() as session:
        if session.scalar(select(Team).limit(1)) is not None:
            return

        backend = Team(name="backend")
        frontend = Team(name="frontend")
        backend.members.extend(
            [
                Member(name="neo"),
                Member(name="trinity"),
            ]
        )
        frontend.members.extend(
            [
                Member(name="morpheus"),
                Member(name="switch"),
            ]
        )
        session.add_all([backend, frontend])
        session.commit()


def member_names(teams: list[Team]) -> list[str]:
    return [member.name for team in teams for member in team.members]


def run_lazy_loading() -> None:
    counter.reset()
    with SessionFactory() as session:
        teams = list(session.scalars(select(Team).order_by(Team.name)))
        print("lazy members:", member_names(teams))
    print("lazy query count:", counter.count)


def run_selectinload() -> None:
    counter.reset()
    with SessionFactory() as session:
        stmt = select(Team).options(selectinload(Team.members)).order_by(Team.name)
        teams = list(session.scalars(stmt))
        print("selectinload members:", member_names(teams))
    print("selectinload query count:", counter.count)


def run_joinedload() -> None:
    counter.reset()
    with SessionFactory() as session:
        stmt = select(Team).options(joinedload(Team.members)).order_by(Team.name)
        teams = list(session.scalars(stmt).unique())
        print("joinedload members:", member_names(teams))
    print("joinedload query count:", counter.count)


def main() -> None:
    seed()
    run_lazy_loading()
    run_selectinload()
    run_joinedload()


if __name__ == "__main__":
    main()
