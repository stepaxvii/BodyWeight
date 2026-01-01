"""update achievement slugs from underscore to kebab-case

Revision ID: 005_update_achievement_slugs
Revises: 004_update_gif_urls
Create Date: 2024-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_update_achievement_slugs'
down_revision: Union[str, None] = '004_update_gif_urls'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mapping from old slugs (underscore) to new slugs (kebab-case)
SLUG_MAPPING = {
    'first_workout': 'first-blood',
    'workout_10': 'workout-10',
    'workout_50': 'workout-50',
    'workout_100': 'centurion',
    'workout_365': 'workout-365',
    'streak_3': 'streak-3',
    'streak_7': 'week-warrior',
    'streak_14': 'streak-14',
    'streak_30': 'month-master',
    'streak_60': 'iron-will',
    'streak_100': 'unstoppable',
    'streak_365': 'streak-365',
    'level_5': 'level-5',
    'level_10': 'level-10',
    'level_25': 'legend',
    'level_50': 'level-50',
    'level_100': 'level-100',
    'early_bird': 'early-bird',
    'night_owl': 'night-owl',
    'pushup_100': 'pushup-100',
    'pushup_500': 'pushup-500',
    'pushup_1000': 'pushup-1000',
    'squat_100': 'squat-100',
    'squat_500': 'squat-500',
    'squat_1000': 'squat-1000',
    'burpee_50': 'burpee-50',
    'burpee_100': 'burpee-100',
    'burpee_500': 'burpee-500',
    'pullup_100': 'pullup-100',
    'pullup_500': 'pullup-500',
    'xp_1000': 'xp-1000',
    'xp_10000': 'xp-10000',
    'xp_100000': 'xp-100000',
}


def upgrade() -> None:
    # Update achievement slugs in user_achievements table
    for old_slug, new_slug in SLUG_MAPPING.items():
        op.execute(
            f"UPDATE user_achievements SET achievement_slug = '{new_slug}' WHERE achievement_slug = '{old_slug}'"
        )


def downgrade() -> None:
    # Reverse the mapping
    for old_slug, new_slug in SLUG_MAPPING.items():
        op.execute(
            f"UPDATE user_achievements SET achievement_slug = '{old_slug}' WHERE achievement_slug = '{new_slug}'"
        )
