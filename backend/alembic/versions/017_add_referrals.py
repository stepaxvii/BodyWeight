"""Add referral program columns to users.

Revision ID: 017_add_referrals
Revises: 016_add_workout_idempotency
Create Date: 2026-10-31

- users.invited_by_user_id: who invited this user via the bot invite link
  (nullable; set once for brand-new / zero-workout users only).
- users.referral_rewards_count: how many of this user's invitees already
  earned them the referral reward (capped in services/referral.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "017_add_referrals"
down_revision: Union[str, None] = "016_add_workout_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "invited_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "referral_rewards_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "referral_rewards_count")
    op.drop_column("users", "invited_by_user_id")
