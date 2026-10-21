"""Add workout submit idempotency + workout_exercise uniqueness.

Revision ID: 016_add_workout_idempotency
Revises: 015_add_sound_enabled
Create Date: 2026-10-21

Fixes duplicate workout recording:
- workout_sessions.client_request_id + UNIQUE(user_id, client_request_id):
  a retried/offline-replayed submit carries the same key, so the server
  returns the existing session instead of creating a duplicate.
- UNIQUE(workout_session_id, exercise_id) on workout_exercises so a single
  exercise can never be recorded twice in one session. Pre-existing duplicate
  rows are merged (summed) into one before the constraint is created.

NULLs are distinct under a UNIQUE index in both SQLite and Postgres, so
legacy rows with a NULL client_request_id coexist fine.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "016_add_workout_idempotency"
down_revision: Union[str, None] = "015_add_sound_enabled"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _merge_duplicate_workout_exercises(bind) -> None:
    """Collapse pre-existing duplicate (workout_session_id, exercise_id) rows.

    Keeps the lowest id, sums the numeric totals of the group into it, and
    deletes the extras — so the new unique index can be created and per-exercise
    totals stay consistent with the (already-summed) workout_sessions totals.
    """
    dup_groups = bind.execute(
        sa.text(
            "SELECT workout_session_id, exercise_id FROM workout_exercises "
            "GROUP BY workout_session_id, exercise_id HAVING COUNT(*) > 1"
        )
    ).fetchall()

    for ws_id, ex_id in dup_groups:
        rows = bind.execute(
            sa.text(
                "SELECT id, sets_completed, total_reps, total_duration_seconds, "
                "xp_earned, coins_earned FROM workout_exercises "
                "WHERE workout_session_id = :w AND exercise_id = :e ORDER BY id"
            ),
            {"w": ws_id, "e": ex_id},
        ).fetchall()

        keep_id = rows[0][0]
        bind.execute(
            sa.text(
                "UPDATE workout_exercises SET sets_completed = :s, total_reps = :r, "
                "total_duration_seconds = :d, xp_earned = :x, coins_earned = :c "
                "WHERE id = :id"
            ),
            {
                "s": sum(r[1] for r in rows),
                "r": sum(r[2] for r in rows),
                "d": sum(r[3] for r in rows),
                "x": sum(r[4] for r in rows),
                "c": sum(r[5] for r in rows),
                "id": keep_id,
            },
        )
        for extra in rows[1:]:
            bind.execute(
                sa.text("DELETE FROM workout_exercises WHERE id = :id"),
                {"id": extra[0]},
            )


def upgrade() -> None:
    op.add_column(
        "workout_sessions",
        sa.Column("client_request_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "uq_workout_user_request",
        "workout_sessions",
        ["user_id", "client_request_id"],
        unique=True,
    )

    _merge_duplicate_workout_exercises(op.get_bind())
    op.create_index(
        "uq_workout_exercise",
        "workout_exercises",
        ["workout_session_id", "exercise_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_workout_exercise", table_name="workout_exercises")
    op.drop_index("uq_workout_user_request", table_name="workout_sessions")
    op.drop_column("workout_sessions", "client_request_id")
