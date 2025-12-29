"""update gif_url for all exercises based on slug

Revision ID: 004_update_gif_urls
Revises: 003_tags_favorites_routines
Create Date: 2024-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_update_gif_urls'
down_revision: Union[str, None] = '003_tags_favorites_routines'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update gif_url for all exercises: set to /sprites/exercises/{slug}.svg
    op.execute(
        "UPDATE exercises SET gif_url = '/sprites/exercises/' || slug || '.svg'"
    )


def downgrade() -> None:
    # Set gif_url back to NULL
    op.execute("UPDATE exercises SET gif_url = NULL")
