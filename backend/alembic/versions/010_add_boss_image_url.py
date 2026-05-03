"""Add image_url to monthly bosses + backfill from data file.

Revision ID: 010_add_boss_image_url
Revises: 009_add_monthly_bosses
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010_add_boss_image_url"
down_revision: Union[str, None] = "009_add_monthly_bosses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "monthly_bosses",
        sa.Column("image_url", sa.String(255), nullable=True),
    )

    # Backfill image_url for any boss that already exists, by slug.
    # Slugs are stable per month, so this is safe.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE monthly_bosses "
            "SET image_url = '/sprites/bosses/' || slug || '.svg' "
            "WHERE image_url IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("monthly_bosses", "image_url")
