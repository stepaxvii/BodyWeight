"""Normalize leaderboard_visible to 0/1 (SQLite stored 'false' as text, bool('false')==True).

Revision ID: 007_normalize_leaderboard_visible
Revises: 006_add_leaderboard_visible
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op


revision: str = "007_normalize_leaderboard_visible"
down_revision: Union[str, None] = "006_add_leaderboard_visible"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite may have stored "false"/"true" as TEXT. Normalize to 0/1 so all readers agree.
    op.execute("""
        UPDATE users SET leaderboard_visible = CASE
            WHEN leaderboard_visible IN (1, '1', 'true', 'true') THEN 1
            ELSE 0
        END
    """)


def downgrade() -> None:
    pass  # no reversible change to data
