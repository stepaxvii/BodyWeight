"""Exercise and category models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


class ExerciseCategory(Base):
    __tablename__ = "exercise_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(7))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    exercises: Mapped[list["Exercise"]] = relationship(back_populates="category")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("exercise_categories.id"))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    description_ru: Mapped[str | None] = mapped_column(Text)

    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    base_xp: Mapped[int] = mapped_column(Integer, default=10)
    required_level: Mapped[int] = mapped_column(Integer, default=1)
    equipment: Mapped[str] = mapped_column(String(20), default="none")
    is_timed: Mapped[bool] = mapped_column(Boolean, default=False)

    gif_url: Mapped[str | None] = mapped_column(String(255))
    thumbnail_url: Mapped[str | None] = mapped_column(String(255))

    easier_exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercises.id"))
    harder_exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercises.id"))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    category: Mapped["ExerciseCategory"] = relationship(back_populates="exercises")
    easier_exercise: Mapped[Optional["Exercise"]] = relationship(
        foreign_keys=[easier_exercise_id], remote_side=[id]
    )
    harder_exercise: Mapped[Optional["Exercise"]] = relationship(
        foreign_keys=[harder_exercise_id], remote_side=[id]
    )

    __table_args__ = (
        CheckConstraint("difficulty >= 1 AND difficulty <= 5", name="check_difficulty_range"),
    )
