"""User exercise progress and favorites."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user import User
from .exercise import Exercise


class UserExerciseProgress(Base):
    __tablename__ = "user_exercise_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))

    total_reps_ever: Mapped[int] = mapped_column(Integer, default=0)
    best_single_set: Mapped[int] = mapped_column(Integer, default=0)
    times_performed: Mapped[int] = mapped_column(Integer, default=0)
    last_performed_at: Mapped[datetime | None] = mapped_column(DateTime)
    recommended_upgrade: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="exercise_progress")
    exercise: Mapped["Exercise"] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_progress"),)


class UserFavoriteExercise(Base):
    __tablename__ = "user_favorite_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="favorite_exercises")
    exercise: Mapped["Exercise"] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "exercise_id", name="uq_user_favorite_exercise"),)