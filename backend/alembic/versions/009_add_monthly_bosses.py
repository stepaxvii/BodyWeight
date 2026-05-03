"""Add monthly bosses and contributions tables.

Revision ID: 009_add_monthly_bosses
Revises: 008_add_web_auth_fields
Create Date: 2026-05-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009_add_monthly_bosses"
down_revision: Union[str, None] = "008_add_web_auth_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_bosses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_ru", sa.String(100), nullable=False),
        sa.Column("image_emoji", sa.String(16), nullable=False),
        sa.Column("theme", sa.String(30), nullable=False),
        sa.Column("legend_ru", sa.Text(), nullable=False),
        sa.Column("max_hp", sa.BigInteger(), nullable=False),
        sa.Column("current_hp", sa.BigInteger(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("defeated_at", sa.DateTime(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("start_date", name="uq_monthly_boss_start"),
    )
    op.create_index("ix_monthly_bosses_start_date", "monthly_bosses", ["start_date"])
    op.create_index("ix_monthly_bosses_end_date", "monthly_bosses", ["end_date"])
    op.create_index("ix_monthly_bosses_status", "monthly_bosses", ["status"])

    op.create_table(
        "boss_contributions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "boss_id",
            sa.Integer(),
            sa.ForeignKey("monthly_bosses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_damage", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("attacks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attack_at", sa.DateTime(), nullable=True),
        sa.Column("reward_tier", sa.String(20), nullable=True),
        sa.Column("reward_coins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_top10", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reward_claimed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("boss_id", "user_id", name="uq_boss_user"),
    )
    op.create_index("idx_boss_user", "boss_contributions", ["boss_id", "user_id"])
    op.create_index("idx_boss_damage", "boss_contributions", ["boss_id", "total_damage"])


def downgrade() -> None:
    op.drop_index("idx_boss_damage", table_name="boss_contributions")
    op.drop_index("idx_boss_user", table_name="boss_contributions")
    op.drop_table("boss_contributions")
    op.drop_index("ix_monthly_bosses_status", table_name="monthly_bosses")
    op.drop_index("ix_monthly_bosses_end_date", table_name="monthly_bosses")
    op.drop_index("ix_monthly_bosses_start_date", table_name="monthly_bosses")
    op.drop_table("monthly_bosses")
