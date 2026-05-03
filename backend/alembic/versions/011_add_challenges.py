"""Add user-created challenges tables.

Revision ID: 011_add_challenges
Revises: 010_add_boss_image_url
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011_add_challenges"
down_revision: Union[str, None] = "010_add_boss_image_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "creator_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="upcoming"),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_challenges_creator", "challenges", ["creator_user_id"])
    op.create_index("ix_challenges_start", "challenges", ["start_date"])
    op.create_index("ix_challenges_end", "challenges", ["end_date"])
    op.create_index("ix_challenges_status", "challenges", ["status"])

    op.create_table(
        "challenge_exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "challenge_id",
            sa.Integer(),
            sa.ForeignKey("challenges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("daily_target", sa.Integer(), nullable=False),
        sa.Column("is_timed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint(
            "challenge_id", "exercise_id", name="uq_challenge_exercise"
        ),
    )
    op.create_index("ix_challenge_exercises_challenge", "challenge_exercises", ["challenge_id"])

    op.create_table(
        "challenge_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "challenge_id",
            sa.Integer(),
            sa.ForeignKey("challenges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("reward_tier", sa.String(20), nullable=True),
        sa.Column("reward_coins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_claimed_at", sa.DateTime(), nullable=True),
        sa.Column("completion_percent", sa.Integer(), nullable=True),
        sa.UniqueConstraint(
            "challenge_id", "user_id", name="uq_challenge_participant"
        ),
    )
    op.create_index("ix_challenge_participants_challenge", "challenge_participants", ["challenge_id"])
    op.create_index("ix_challenge_participants_user", "challenge_participants", ["user_id"])

    op.create_table(
        "challenge_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "challenge_id",
            sa.Integer(),
            sa.ForeignKey("challenges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("progress_date", sa.Date(), nullable=False),
        sa.Column("accumulated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint(
            "challenge_id",
            "user_id",
            "exercise_id",
            "progress_date",
            name="uq_progress_dim",
        ),
    )
    op.create_index("idx_progress_user_date", "challenge_progress", ["user_id", "progress_date"])
    op.create_index("idx_progress_challenge_date", "challenge_progress", ["challenge_id", "progress_date"])


def downgrade() -> None:
    op.drop_index("idx_progress_challenge_date", table_name="challenge_progress")
    op.drop_index("idx_progress_user_date", table_name="challenge_progress")
    op.drop_table("challenge_progress")

    op.drop_index("ix_challenge_participants_user", table_name="challenge_participants")
    op.drop_index("ix_challenge_participants_challenge", table_name="challenge_participants")
    op.drop_table("challenge_participants")

    op.drop_index("ix_challenge_exercises_challenge", table_name="challenge_exercises")
    op.drop_table("challenge_exercises")

    op.drop_index("ix_challenges_status", table_name="challenges")
    op.drop_index("ix_challenges_end", table_name="challenges")
    op.drop_index("ix_challenges_start", table_name="challenges")
    op.drop_index("ix_challenges_creator", table_name="challenges")
    op.drop_table("challenges")
