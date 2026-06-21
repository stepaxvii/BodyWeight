"""Add per-exercise personal-record columns (best_workout_reps, best_single_day).

Revision ID: 014_add_exercise_records
Revises: 013_add_activity_norms
Create Date: 2026-06-13

Powers roadmap 2.3 (Личные рекорды) / 2.4 (Статистика по упражнению):
- best_workout_reps: max reps for this exercise in a single workout.
- best_single_day: max reps for this exercise across a single calendar day.
Existing rows backfill to 0; the workout processor fills them going forward.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "014_add_exercise_records"
down_revision: Union[str, None] = "013_add_activity_norms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_exercise_progress",
        sa.Column("best_workout_reps", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_exercise_progress",
        sa.Column("best_single_day", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("user_exercise_progress", "best_single_day")
    op.drop_column("user_exercise_progress", "best_workout_reps")
