"""add RPG district quest fields

Revision ID: 023_add_quest_fields
Revises: 022_drop_web_auth_fields
Create Date: 2026-11-06

Adds the quest layer on top of the existing challenge engine:
- challenges.quest_id        — marks a challenge as a materialized district quest
                               (NULL = ordinary user challenge). Indexed: every
                               isolation seam filters on it.
- challenges.mercenary_avatar — cosmetic co-op companion for friendless players
                               (render-only; never a participant).
- challenge_participants.invite_status — co-op invite consent
                               (None | pending | accepted | declined).
- user_quest_completions     — per-user quest completion facts (drive unlocks).

SQLite notes: ADD COLUMN needs no batch. In downgrade a column that carries an
index must have the index dropped BEFORE the batch table-copy, else alembic
recreates it on the now-missing column ("no such column") — see 022.
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_add_quest_fields"
down_revision: Union[str, None] = "022_drop_web_auth_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # challenges.quest_id (+ index — all seams filter by it)
    op.add_column("challenges", sa.Column("quest_id", sa.String(length=64), nullable=True))
    op.create_index("ix_challenges_quest_id", "challenges", ["quest_id"])
    # challenges.mercenary_avatar (render-only, no index)
    op.add_column("challenges", sa.Column("mercenary_avatar", sa.String(length=64), nullable=True))
    # challenge_participants.invite_status (+ index — lock/wait-for-all filter by it)
    op.add_column(
        "challenge_participants",
        sa.Column("invite_status", sa.String(length=16), nullable=True),
    )
    op.create_index(
        "ix_challenge_participants_invite_status",
        "challenge_participants",
        ["invite_status"],
    )
    # user_quest_completions
    op.create_table(
        "user_quest_completions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quest_id", sa.String(length=64), nullable=False),
        sa.Column("district_id", sa.String(length=64), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),
    )
    op.create_index(
        "ix_user_quest_completions_user_id", "user_quest_completions", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_quest_completions_user_id", table_name="user_quest_completions")
    op.drop_table("user_quest_completions")

    # drop indexes BEFORE batch table-copy (SQLite gotcha)
    op.drop_index(
        "ix_challenge_participants_invite_status",
        table_name="challenge_participants",
    )
    with op.batch_alter_table("challenge_participants") as batch_op:
        batch_op.drop_column("invite_status")

    op.drop_index("ix_challenges_quest_id", table_name="challenges")
    with op.batch_alter_table("challenges") as batch_op:
        batch_op.drop_column("mercenary_avatar")
        batch_op.drop_column("quest_id")
