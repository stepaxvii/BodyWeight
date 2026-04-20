"""add leaderboard_visible to users

Revision ID: 006_add_leaderboard_visible
Revises: 67aca3c3bf83
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '006_add_leaderboard_visible'
down_revision: Union[str, None] = '67aca3c3bf83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('leaderboard_visible', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('users', 'leaderboard_visible')
