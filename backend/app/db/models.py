from datetime import datetime, date, time
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    Date,
    Time,
    Numeric,
    UniqueConstraint,
    Index,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_id: Mapped[str] = mapped_column(String(50), default="wolf")

    # Gamification
    level: Mapped[int] = mapped_column(Integer, default=1)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    coins: Mapped[int] = mapped_column(Integer, default=0)

    # Streaks
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_workout_date: Mapped[Optional[date]] = mapped_column(Date)

    # Settings
    notification_time: Mapped[Optional[time]] = mapped_column(Time)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Onboarding
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    workout_sessions: Mapped[List["WorkoutSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[List["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[List["UserGoal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    purchases: Mapped[List["UserPurchase"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    exercise_progress: Mapped[List["UserExerciseProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    favorite_exercises: Mapped[List["UserFavoriteExercise"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    custom_routines: Mapped[List["UserCustomRoutine"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ExerciseCategory(Base):
    __tablename__ = "exercise_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(7))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    exercises: Mapped[List["Exercise"]] = relationship(back_populates="category")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("exercise_categories.id"))
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    description_ru: Mapped[Optional[str]] = mapped_column(Text)

    # Tags for filtering (muscle groups, level, equipment, etc.)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Difficulty & progression
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    base_xp: Mapped[int] = mapped_column(Integer, default=10)
    required_level: Mapped[int] = mapped_column(Integer, default=1)

    # Equipment required: none, pullup-bar, dip-bars, bench, wall
    equipment: Mapped[str] = mapped_column(String(20), default="none")

    # True for time-based exercises (planks, stretches, etc.)
    is_timed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Media
    gif_url: Mapped[Optional[str]] = mapped_column(String(255))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(255))

    # Progression chain
    easier_exercise_id: Mapped[Optional[int]] = mapped_column(ForeignKey("exercises.id"))
    harder_exercise_id: Mapped[Optional[int]] = mapped_column(ForeignKey("exercises.id"))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
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


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Totals
    total_xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    total_coins_earned: Mapped[int] = mapped_column(Integer, default=0)
    total_reps: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)  # Time for static exercises

    # Streak bonus applied
    streak_multiplier: Mapped[float] = mapped_column(Numeric(3, 2), default=1.00)

    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, cancelled

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    exercises: Mapped[List["WorkoutExercise"]] = relationship(back_populates="workout_session", cascade="all, delete-orphan")


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))

    sets_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_reps: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)  # For time-based exercises

    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    coins_earned: Mapped[int] = mapped_column(Integer, default=0)

    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    workout_session: Mapped["WorkoutSession"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_slug: Mapped[str] = mapped_column(String(100), nullable=False)

    unlocked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="achievements")

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_slug", name="uq_user_achievement"),
    )


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # weekly_workouts, daily_xp, specific_exercise
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, default=0)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="goals")


class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, blocked

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friendship"),
        Index("idx_friendships_user_status", "user_id", "status"),
    )


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)

    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # title, badge, theme

    price_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, default=1)

    sprite_url: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    purchases: Mapped[List["UserPurchase"]] = relationship(back_populates="shop_item")


class UserPurchase(Base):
    __tablename__ = "user_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    shop_item_id: Mapped[int] = mapped_column(ForeignKey("shop_items.id"))

    purchased_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="purchases")
    shop_item: Mapped["ShopItem"] = relationship(back_populates="purchases")

    __table_args__ = (
        UniqueConstraint("user_id", "shop_item_id", name="uq_user_purchase"),
    )


class UserExerciseProgress(Base):
    __tablename__ = "user_exercise_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))

    total_reps_ever: Mapped[int] = mapped_column(Integer, default=0)
    best_single_set: Mapped[int] = mapped_column(Integer, default=0)
    times_performed: Mapped[int] = mapped_column(Integer, default=0)
    last_performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # For progression recommendations
    recommended_upgrade: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="exercise_progress")
    exercise: Mapped["Exercise"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_user_exercise_progress"),
    )


class UserFavoriteExercise(Base):
    """User's favorite exercises for quick access."""
    __tablename__ = "user_favorite_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="favorite_exercises")
    exercise: Mapped["Exercise"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_user_favorite_exercise"),
    )


class UserCustomRoutine(Base):
    """User-created custom workout routines."""
    __tablename__ = "user_custom_routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Routine type: morning, workout, stretch
    routine_type: Mapped[str] = mapped_column(String(50), default="workout")

    # Estimated duration in minutes
    duration_minutes: Mapped[int] = mapped_column(Integer, default=15)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="custom_routines")
    exercises: Mapped[List["UserCustomRoutineExercise"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan", order_by="UserCustomRoutineExercise.sort_order"
    )


class UserCustomRoutineExercise(Base):
    """Exercises within a user's custom routine."""
    __tablename__ = "user_custom_routine_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(ForeignKey("user_custom_routines.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))

    # Order in the routine
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Target reps or duration (seconds for timed exercises)
    target_reps: Mapped[Optional[int]] = mapped_column(Integer)
    target_duration: Mapped[Optional[int]] = mapped_column(Integer)

    # Rest time after this exercise (seconds)
    rest_seconds: Mapped[int] = mapped_column(Integer, default=30)

    # Relationships
    routine: Mapped["UserCustomRoutine"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()
