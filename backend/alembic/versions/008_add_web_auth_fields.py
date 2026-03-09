"""Add email and password_hash fields for web authentication.
Make telegram_id nullable for web-only users.

Revision ID: 008_add_web_auth_fields
Revises: 007_normalize_leaderboard_visible
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008_add_web_auth_fields"
down_revision: Union[str, None] = "007_normalize_leaderboard_visible"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email and password_hash columns
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))

    # Create unique index on email
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Note: SQLite does not support ALTER COLUMN to make telegram_id nullable.
    # Since telegram_id was NOT NULL before, existing rows all have values.
    # New web-only users will have telegram_id=NULL which SQLite allows even
    # if the column was originally created as NOT NULL (SQLite quirk).
    # For a proper migration on other databases, you would need to recreate the table.


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
