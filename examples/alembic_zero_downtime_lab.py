from __future__ import annotations

# What this lab adds / 이 예제가 추가하는 것:
# - Show an expand -> dual read/write -> backfill flow with SQLite and SQLAlchemy.
# - SQLite와 SQLAlchemy로 expand -> dual read/write -> backfill 흐름을 보여준다.
# - Show why additive changes are safer than destructive one-shot renames.
# - 파괴적 one-shot rename보다 additive change가 왜 안전한지 보여준다.
#
# Why it was added / 왜 추가되었나:
# - Migration advice stays vague unless rollout compatibility is executable.
# - rollout compatibility는 실행해보지 않으면 감이 잘 안 잡힌다.
# - Alembic is most useful when teams think in staged deployment, not only DDL text.
# - Alembic은 DDL 문장보다 단계적 배포 사고방식과 같이 봐야 의미가 크다.
#
# When to use this / 언제 보면 좋은가:
# - When planning a column rename without downtime.
# - 다운타임 없이 column rename 비슷한 작업을 계획할 때.
# - When reviewing whether old app / new schema combinations are safe.
# - old app / new schema 조합이 안전한지 리뷰할 때.
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.engine import Engine

metadata = MetaData()


def create_initial_schema(engine: Engine) -> None:
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("full_name", String(100), nullable=False),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(users.insert(), [{"full_name": "Neo Anderson"}])


def print_rows(engine: Engine, title: str) -> None:
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT id, full_name, display_name FROM users ORDER BY id")).mappings().all()
    print(f"\n== {title} ==")
    for row in rows:
        print(dict(row))


def expand_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))


def app_v2_insert(engine: Engine, *, full_name: str, display_name: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (full_name, display_name)
                VALUES (:full_name, :display_name)
                """
            ),
            {"full_name": full_name, "display_name": display_name},
        )


def app_v2_read(engine: Engine) -> list[dict[str, str | int | None]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, full_name, COALESCE(display_name, full_name) AS effective_display_name
                FROM users
                ORDER BY id
                """
            )
        ).mappings()
        return [dict(row) for row in rows]


def backfill_display_name(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE users
                SET display_name = full_name
                WHERE display_name IS NULL
                """
            )
        )


def main() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    create_initial_schema(engine)
    expand_schema(engine)
    print_rows(engine, "after expand")

    app_v2_insert(
        engine,
        full_name="Trinity",
        display_name="Trinity",
    )
    print_rows(engine, "after new app dual write")

    backfill_display_name(engine)
    print_rows(engine, "after backfill")

    print("\n== new app dual read ==")
    for row in app_v2_read(engine):
        print(row)

    print("\ncontract step should happen last: drop full_name only after old app is gone")


if __name__ == "__main__":
    main()
