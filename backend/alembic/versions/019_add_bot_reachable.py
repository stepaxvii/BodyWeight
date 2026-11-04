"""Add users.bot_reachable (can the bot actually deliver to this user).

Revision ID: 019_add_bot_reachable
Revises: 018_add_bot_blocked
Create Date: 2026-11-01

False once a send hits "chat not found" / "user is deactivated" (the user has
a telegram_id but never started THIS bot — common right after a bot migration).
Flips back True on the my_chat_member "member" update. Defaults True (assume
reachable until a send proves otherwise). Powers the digest's honest
promo-reachable count.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "019_add_bot_reachable"
down_revision: Union[str, None] = "018_add_bot_blocked"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "bot_reachable",
            sa.Boolean(),
            nullable=False,
            # "1" (not "true"): SQLite stores the literal string truthy.
            server_default="1",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "bot_reachable")
