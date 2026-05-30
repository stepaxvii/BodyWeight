"""User model."""
from datetime import datetime, date, time
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from ..types import BooleanCoerce


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    avatar_id: Mapped[str] = mapped_column(String(50), default="shadow-wolf")

    # Web auth fields
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Gamification
    level: Mapped[int] = mapped_column(Integer, default=1)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    coins: Mapped[int] = mapped_column(Integer, default=0)

    # Streaks
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_workout_date: Mapped[date | None] = mapped_column(Date)
    # Purchased "streak freezes" — auto-spent overnight to cover a missed day
    streak_freezes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Settings
    notification_time: Mapped[time | None] = mapped_column(Time)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Onboarding
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    leaderboard_visible: Mapped[bool] = mapped_column(BooleanCoerce, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    workout_sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["UserGoal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    purchases: Mapped[list["UserPurchase"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    exercise_progress: Mapped[list["UserExerciseProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favorite_exercises: Mapped[list["UserFavoriteExercise"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    custom_routines: Mapped[list["UserCustomRoutine"]] = relationship(back_populates="user", cascade="all, delete-orphan")
