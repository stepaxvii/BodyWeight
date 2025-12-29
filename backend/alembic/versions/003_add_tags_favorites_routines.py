"""add tags to exercises, user favorites and custom routines

Revision ID: 003_tags_favorites_routines
Revises: 002_add_equipment
Create Date: 2024-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_tags_favorites_routines'
down_revision: Union[str, None] = '002_add_equipment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tags column to exercises (JSON array)
    op.add_column('exercises', sa.Column('tags', sa.JSON(), nullable=True, server_default='[]'))

    # Create user_favorite_exercises table
    op.create_table(
        'user_favorite_exercises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'exercise_id', name='uq_user_favorite_exercise')
    )
    op.create_index('ix_user_favorite_exercises_user_id', 'user_favorite_exercises', ['user_id'])

    # Create user_custom_routines table
    op.create_table(
        'user_custom_routines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('routine_type', sa.String(50), nullable=False, server_default='workout'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_custom_routines_user_id', 'user_custom_routines', ['user_id'])

    # Create user_custom_routine_exercises table
    op.create_table(
        'user_custom_routine_exercises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('routine_id', sa.Integer(), nullable=False),
        sa.Column('exercise_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_reps', sa.Integer(), nullable=True),
        sa.Column('target_duration', sa.Integer(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.ForeignKeyConstraint(['routine_id'], ['user_custom_routines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_custom_routine_exercises_routine_id', 'user_custom_routine_exercises', ['routine_id'])


def downgrade() -> None:
    op.drop_table('user_custom_routine_exercises')
    op.drop_table('user_custom_routines')
    op.drop_table('user_favorite_exercises')
    op.drop_column('exercises', 'tags')
