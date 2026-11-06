"""add users.timezone (IANA name)

Revision ID: 024_add_user_timezone
Revises: 023_add_quest_fields
Create Date: 2026-11-07

Adds users.timezone — the player's IANA zone name ("Europe/Moscow", ...), default
"UTC". All day-boundary logic (streaks, quest days, end-of-day checks) and the
local daily-reminder time are computed in this zone. Existing rows backfill to
"UTC" via the server_default (identical to today's behaviour → no regression); the
client auto-detects and updates it on next open, and it is overridable in Settings.
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_add_user_timezone"
down_revision: Union[str, None] = "023_add_quest_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
