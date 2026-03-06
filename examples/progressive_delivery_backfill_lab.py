from __future__ import annotations

# What this lab adds / 이 예제가 추가하는 것:
# - Show a resumable chunked backfill with checkpoints.
# - checkpoint 기반 resumable chunked backfill을 보여준다.
# - Show why backfill is usually a separate operational job from Alembic DDL.
# - backfill이 왜 Alembic DDL과 분리된 운영 job이 되는지 보여준다.
#
# Why it was added / 왜 추가되었나:
# - Zero-downtime migration advice stays abstract unless resume/throttle/checkpoint shape is executable.
# - zero-downtime migration은 resume/throttle/checkpoint 모양이 코드로 보여야 감이 온다.
# - Progressive delivery still depends on safe schema and data rollout.
# - progressive delivery도 결국 schema/data rollout 안전성이 바탕이다.
#
# When to use this / 언제 보면 좋은가:
# - When planning a large backfill after an expand migration.
# - expand migration 뒤 큰 backfill을 계획할 때.
# - When designing a restart-safe migration worker.
# - 재시작에 안전한 migration worker를 설계할 때.
from dataclasses import dataclass

from sqlalchemy import Engine, create_engine, text


@dataclass(frozen=True, slots=True)
class BackfillBatchResult:
    processed_rows: int
    last_processed_id: int
    is_complete: bool


def create_initial_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO users (id, full_name) VALUES
                    (1, 'Neo Anderson'),
                    (2, 'Trinity'),
                    (3, 'Morpheus'),
                    (4, 'Oracle'),
                    (5, 'Niobe')
                """
            )
        )


def expand_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS backfill_checkpoints (
                    job_name VARCHAR(100) PRIMARY KEY,
                    last_processed_id INTEGER NOT NULL,
                    updated_rows INTEGER NOT NULL
                )
                """
            )
        )


def load_checkpoint(engine: Engine, job_name: str) -> tuple[int, int]:
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT last_processed_id, updated_rows
                FROM backfill_checkpoints
                WHERE job_name = :job_name
                """
            ),
            {"job_name": job_name},
        ).mappings().first()

    if row is None:
        return 0, 0
    return int(row["last_processed_id"]), int(row["updated_rows"])


def save_checkpoint(
    engine: Engine,
    job_name: str,
    *,
    last_processed_id: int,
    updated_rows: int,
) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO backfill_checkpoints (job_name, last_processed_id, updated_rows)
                VALUES (:job_name, :last_processed_id, :updated_rows)
                ON CONFLICT(job_name) DO UPDATE SET
                    last_processed_id = excluded.last_processed_id,
                    updated_rows = excluded.updated_rows
                """
            ),
            {
                "job_name": job_name,
                "last_processed_id": last_processed_id,
                "updated_rows": updated_rows,
            },
        )


def run_backfill_batch(engine: Engine, *, job_name: str, batch_size: int) -> BackfillBatchResult:
    checkpoint_id, updated_rows = load_checkpoint(engine, job_name)

    with engine.begin() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, full_name
                FROM users
                WHERE id > :checkpoint_id
                  AND display_name IS NULL
                ORDER BY id
                LIMIT :batch_size
                """
            ),
            {"checkpoint_id": checkpoint_id, "batch_size": batch_size},
        ).mappings().all()

        if not rows:
            return BackfillBatchResult(
                processed_rows=0,
                last_processed_id=checkpoint_id,
                is_complete=True,
            )

        for row in rows:
            connection.execute(
                text(
                    """
                    UPDATE users
                    SET display_name = full_name
                    WHERE id = :user_id
                      AND display_name IS NULL
                    """
                ),
                {"user_id": row["id"]},
            )

        new_checkpoint_id = int(rows[-1]["id"])
        new_updated_rows = updated_rows + len(rows)

    save_checkpoint(
        engine,
        job_name,
        last_processed_id=new_checkpoint_id,
        updated_rows=new_updated_rows,
    )

    return BackfillBatchResult(
        processed_rows=len(rows),
        last_processed_id=new_checkpoint_id,
        is_complete=False,
    )


def print_state(engine: Engine, title: str) -> None:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, full_name, display_name
                FROM users
                ORDER BY id
                """
            )
        ).mappings().all()

    print(f"\n== {title} ==")
    for row in rows:
        print(dict(row))


def main() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    job_name = "users_display_name_backfill"

    create_initial_schema(engine)
    expand_schema(engine)
    print_state(engine, "after expand migration")

    first_batch = run_backfill_batch(engine, job_name=job_name, batch_size=2)
    print(f"\nfirst batch -> {first_batch}")
    print_state(engine, "after first batch")

    print("\nworker interrupted; resuming from checkpoint")
    second_batch = run_backfill_batch(engine, job_name=job_name, batch_size=2)
    third_batch = run_backfill_batch(engine, job_name=job_name, batch_size=2)
    final_pass = run_backfill_batch(engine, job_name=job_name, batch_size=2)

    print(f"second batch -> {second_batch}")
    print(f"third batch -> {third_batch}")
    print(f"final pass -> {final_pass}")
    print_state(engine, "after resumed completion")

    checkpoint = load_checkpoint(engine, job_name)
    print(f"\ncheckpoint -> last_processed_id={checkpoint[0]}, updated_rows={checkpoint[1]}")


if __name__ == "__main__":
    main()
