"""Add streak_freezes counter to users.

Revision ID: 012_add_streak_freezes
Revises: 011_add_challenges
Create Date: 2026-05-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "012_add_streak_freezes"
down_revision: Union[str, None] = "011_add_challenges"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "streak_freezes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "streak_freezes")
