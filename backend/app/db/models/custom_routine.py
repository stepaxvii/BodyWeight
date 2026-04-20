"""User custom routines."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user import User
from .exercise import Exercise


class UserCustomRoutine(Base):
    __tablename__ = "user_custom_routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    routine_type: Mapped[str] = mapped_column(String(50), default="workout")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="custom_routines")
    exercises: Mapped[list["UserCustomRoutineExercise"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan", order_by="UserCustomRoutineExercise.sort_order"
    )


class UserCustomRoutineExercise(Base):
    __tablename__ = "user_custom_routine_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(ForeignKey("user_custom_routines.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    target_reps: Mapped[int | None] = mapped_column(Integer)
    target_duration: Mapped[int | None] = mapped_column(Integer)
    rest_seconds: Mapped[int] = mapped_column(Integer, default=30)

    routine: Mapped["UserCustomRoutine"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()
