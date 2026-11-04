"""add users.language preference

Revision ID: 020_add_user_language
Revises: 019_add_bot_reachable
Create Date: 2026-11-04

Adds users.language ('ru' | 'en'). Existing users are backfilled to 'ru' via the
server_default (they predate i18n and were Russian-only). New users get their
language set explicitly by the bot on first /start, detected from the Telegram
client language_code with an English fallback.
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_add_user_language"
down_revision: Union[str, None] = "019_add_bot_reachable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("language", sa.String(length=5), nullable=False, server_default="ru"),
    )


def downgrade() -> None:
    op.drop_column("users", "language")
