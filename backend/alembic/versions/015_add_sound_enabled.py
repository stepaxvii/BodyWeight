"""Add users.sound_enabled (8-bit sound effects toggle, roadmap 5.1).

Revision ID: 015_add_sound_enabled
Revises: 014_add_exercise_records
Create Date: 2026-06-14

Existing users default to sound on (server_default "1").
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "015_add_sound_enabled"
down_revision: Union[str, None] = "014_add_exercise_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("sound_enabled", sa.Boolean(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("users", "sound_enabled")
