"""add equipment to exercises

Revision ID: 002_add_equipment
Revises: 001_add_is_onboarded
Create Date: 2024-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_equipment'
down_revision: Union[str, None] = '001_add_is_onboarded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exercises', sa.Column('equipment', sa.String(20), nullable=False, server_default='none'))


def downgrade() -> None:
    op.drop_column('exercises', 'equipment')
