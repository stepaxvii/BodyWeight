"""drop web-auth fields (users.email, users.password_hash)

Revision ID: 022_drop_web_auth_fields
Revises: 021_add_boss_legend_en
Create Date: 2026-11-05

The browser email/password login flow was removed — the app is a Telegram
Mini App only. These columns (added in 008_add_web_auth_fields) are now dead,
so drop them. SQLite requires batch mode to rebuild the table; dropping the
email column also removes its unique index.
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_drop_web_auth_fields"
down_revision: Union[str, None] = "021_add_boss_legend_en"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_hash")
        batch_op.drop_column("email")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_users_email", ["email"], unique=True)
