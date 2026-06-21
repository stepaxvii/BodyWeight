"""Workout session and workout exercise models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user import User
from .exercise import Exercise


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    total_xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    total_coins_earned: Mapped[int] = mapped_column(Integer, default=0)
    total_reps: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    streak_multiplier: Mapped[float] = mapped_column(Numeric(3, 2), default=1.00)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout_session", cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)

    sets_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_reps: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    coins_earned: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    workout_session: Mapped["WorkoutSession"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()