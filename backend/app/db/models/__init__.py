"""SQLAlchemy models — импорты в порядке зависимостей."""
from .user import User
from .exercise import ExerciseCategory, Exercise
from .workout import WorkoutSession, WorkoutExercise
from .achievement import UserAchievement
from .goal import UserGoal
from .friendship import Friendship
from .shop import ShopItem, UserPurchase, UserAvatarPurchase
from .user_exercise import UserExerciseProgress, UserFavoriteExercise
from .custom_routine import UserCustomRoutine, UserCustomRoutineExercise
from .notification import Notification
from .boss import MonthlyBoss, BossContribution

__all__ = [
    "User",
    "ExerciseCategory",
    "Exercise",
    "WorkoutSession",
    "WorkoutExercise",
    "UserAchievement",
    "UserGoal",
    "Friendship",
    "ShopItem",
    "UserPurchase",
    "UserAvatarPurchase",
    "UserExerciseProgress",
    "UserFavoriteExercise",
    "UserCustomRoutine",
    "UserCustomRoutineExercise",
    "Notification",
    "MonthlyBoss",
    "BossContribution",
]
