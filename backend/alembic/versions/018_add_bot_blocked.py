"""Add users.bot_blocked (tracks who blocked the bot).

Revision ID: 018_add_bot_blocked
Revises: 017_add_referrals
Create Date: 2026-11-01

Set from the bot's my_chat_member update (and defensively on a 403 while
sending). Feeds the admin digest's reachable-audience / blocked counts.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "018_add_bot_blocked"
down_revision: Union[str, None] = "017_add_referrals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "bot_blocked",
            sa.Boolean(),
            nullable=False,
            # "0" (not "false"): SQLite stores the literal string truthy.
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "bot_blocked")
