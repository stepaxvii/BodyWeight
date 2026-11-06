"""User-created challenge models."""
from datetime import datetime, date
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user import User
from .exercise import Exercise


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # 'upcoming' | 'active' | 'finished'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="upcoming", index=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # RPG districts quest layer. quest_id NOT NULL => this challenge is a
    # materialized district quest (from districts.json), NOT a user challenge.
    # It stays out of the public challenge catalog, tier-finalize and claim
    # (see services.challenges isolation seams). NULL => ordinary challenge.
    quest_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Cosmetic hired companion for a solo player with no friends (render-only;
    # NOT a ChallengeParticipant — must never gate wait-for-all or the lock).
    mercenary_avatar: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    creator: Mapped[User | None] = relationship(foreign_keys=[creator_user_id])
    exercises: Mapped[list["ChallengeExercise"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )
    participants: Mapped[list["ChallengeParticipant"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )
    progress_entries: Mapped[list["ChallengeProgress"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class ChallengeExercise(Base):
    __tablename__ = "challenge_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT")
    )
    daily_target: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshot of exercise.is_timed at creation time so semantics don't drift.
    is_timed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    challenge: Mapped[Challenge] = relationship(back_populates="exercises")
    exercise: Mapped[Exercise] = relationship()

    __table_args__ = (
        UniqueConstraint("challenge_id", "exercise_id", name="uq_challenge_exercise"),
    )


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Awarded at finalization
    reward_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reward_coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reward_claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Cached % completion at finalization (0-100). Null until finalized.
    completion_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Co-op quest invite consent (only meaningful for quest challenges):
    #   None  — solo participant / the inviter (no invite)
    #   'pending'  — invited friend who has not answered yet
    #   'accepted' — friend accepted (consumes their one-active-quest lock)
    #   'declined' — friend declined
    # The lock (§4.9) and wait-for-all (§4.7) count only NULL + 'accepted'.
    invite_status: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    challenge: Mapped[Challenge] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()

    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uq_challenge_participant"),
    )


class ChallengeProgress(Base):
    __tablename__ = "challenge_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT")
    )
    progress_date: Mapped[date] = mapped_column(Date, nullable=False)
    accumulated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    challenge: Mapped[Challenge] = relationship(back_populates="progress_entries")

    __table_args__ = (
        UniqueConstraint(
            "challenge_id",
            "user_id",
            "exercise_id",
            "progress_date",
            name="uq_progress_dim",
        ),
        Index("idx_progress_user_date", "user_id", "progress_date"),
        Index("idx_progress_challenge_date", "challenge_id", "progress_date"),
    )


class UserQuestCompletion(Base):
    """A player finished a district quest — the fact used to compute unlocks.

    Written per-participant the moment their full_days >= quest.days (not on the
    shared instance). State of a district (locked/available/active/completed) is
    derived on the fly from districts.json unlock rules + this table, so no
    per-district status column is persisted.
    """
    __tablename__ = "user_quest_completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    quest_id: Mapped[str] = mapped_column(String(64), nullable=False)
    district_id: Mapped[str] = mapped_column(String(64), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),
    )
