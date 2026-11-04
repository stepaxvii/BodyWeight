"""add monthly_bosses.legend_en (English legend)

Revision ID: 021_add_boss_legend_en
Revises: 020_add_user_language
Create Date: 2026-11-04

Adds monthly_bosses.legend_en, the English translation of the boss legend. It is
nullable: existing rows predate i18n (Russian-only legend_ru) and the English
copy is backfilled from data/bosses.json. English is the fallback language.
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_add_boss_legend_en"
down_revision: Union[str, None] = "020_add_user_language"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monthly_bosses",
        sa.Column("legend_en", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("monthly_bosses", "legend_en")
