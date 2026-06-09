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
