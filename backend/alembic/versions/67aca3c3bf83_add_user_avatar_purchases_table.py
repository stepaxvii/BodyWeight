"""add_user_avatar_purchases_table

Revision ID: 67aca3c3bf83
Revises: 005_update_achievement_slugs
Create Date: 2026-01-01 18:04:22.621132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67aca3c3bf83'
down_revision: Union[str, None] = '005_update_achievement_slugs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists (for cases where it was created manually)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if 'user_avatar_purchases' in tables:
        # Table already exists, skip creation
        return

    # Create user_avatar_purchases table
    op.create_table(
        'user_avatar_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('avatar_id', sa.String(length=50), nullable=False),
        sa.Column(
            'purchased_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'avatar_id',
            name='uq_user_avatar_purchase'
        )
    )
    # Create index on user_id for faster lookups
    op.create_index(
        'ix_user_avatar_purchases_user_id',
        'user_avatar_purchases',
        ['user_id']
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index(
        'ix_user_avatar_purchases_user_id',
        table_name='user_avatar_purchases'
    )
    # Drop table
    op.drop_table('user_avatar_purchases')
