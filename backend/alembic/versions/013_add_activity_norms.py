"""Add per-user daily activity norm (current column + versioned history).

Revision ID: 013_add_activity_norms
Revises: 012_add_streak_freezes
Create Date: 2026-06-09

Backfill rules:
- Every existing user: norm 1000 from the start of the project through 2026-05-29.
- From 2026-05-30: norm 2500 for everyone, except user id=1 who gets 1400.
- The current-norm column reflects the era in force today (2500, or 1400 for id=1).
- New users created after this migration default to 1400.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "013_add_activity_norms"
down_revision: Union[str, None] = "012_add_streak_freezes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Current-norm column on users (powers UserResponse + settings UI).
    op.add_column(
        "users",
        sa.Column(
            "daily_activity_norm",
            sa.Integer(),
            nullable=False,
            server_default="1400",
        ),
    )

    # 2. Versioned history table (powers per-day calendar colouring).
    op.create_table(
        "user_activity_norms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("norm", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "effective_from", name="uq_activity_norm_user_date"
        ),
    )
    op.create_index(
        "ix_user_activity_norms_user_id", "user_activity_norms", ["user_id"]
    )

    # 3. Set the current norm on existing users (era2 is in force today).
    op.execute(
        "UPDATE users SET daily_activity_norm = "
        "CASE WHEN id = 1 THEN 1400 ELSE 2500 END"
    )

    # 4. Backfill history.
    #    era1: 1000 from the dawn of the project (covers everything <= 2026-05-29).
    op.execute(
        "INSERT INTO user_activity_norms (user_id, norm, effective_from, created_at) "
        "SELECT id, 1000, '2020-01-01', CURRENT_TIMESTAMP FROM users"
    )
    #    era2: 2500 from 2026-05-30 (1400 for user id=1).
    op.execute(
        "INSERT INTO user_activity_norms (user_id, norm, effective_from, created_at) "
        "SELECT id, CASE WHEN id = 1 THEN 1400 ELSE 2500 END, '2026-05-30', "
        "CURRENT_TIMESTAMP FROM users"
    )


def downgrade() -> None:
    op.drop_index("ix_user_activity_norms_user_id", table_name="user_activity_norms")
    op.drop_table("user_activity_norms")
    op.drop_column("users", "daily_activity_norm")
