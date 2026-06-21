"""Pydantic schemas for API requests and responses."""

from .common import PaginatedResponse
from .users import (
    UserResponse,
    UserStatsResponse,
    UpdateUserRequest,
    CompleteOnboardingRequest,
    UserProfileResponse,
    ExerciseRecord,
    UserRecordsResponse,
    DayActivityResponse,
    UserActivityResponse,
)
from .auth import (
    AuthRequest,
    AuthResponse,
    WebAuthResponse,
    WebRegisterRequest,
    WebLoginRequest,
    SetPasswordRequest,
    LinkTelegramRequest,
    ConfirmLinkResponse,
)
from .workouts import (
    ExerciseSetData,
    CompleteWorkoutRequest,
    WorkoutExerciseResponse,
    WorkoutResponse,
    WorkoutSummaryResponse,
    TodayStatsResponse,
)
from .exercises import (
    CategoryResponse,
    ExerciseResponse,
    ExerciseProgressResponse,
    ExerciseWithProgressResponse,
    RoutineExerciseResponse,
    RoutineResponse,
    FavoriteResponse,
)
from .goals import CreateGoalRequest, GoalResponse
from .friends import FriendResponse, AddFriendRequest
from .achievements import AchievementResponse, RecentAchievementResponse
from .leaderboard import LeaderboardEntry, LeaderboardResponse
from .shop import ShopItemResponse, InventoryItemResponse
from .notifications import NotificationResponse, UnreadCountResponse
from .custom_routines import (
    RoutineExerciseCreate,
    RoutineExerciseResponse,
    CustomRoutineCreate,
    CustomRoutineUpdate,
    CustomRoutineResponse,
    CustomRoutineListItem,
)
from .boss import (
    BossResponse,
    BossLeaderboardEntry,
    BossLeaderboardResponse,
    BossMyContributionResponse,
    BossClaimResponse,
    BossHistoryEntry,
    BossHistoryResponse,
)
from .challenges import (
    ChallengeExerciseCreate,
    ChallengeCreate,
    ChallengeExerciseResponse,
    ChallengeListItem,
    ChallengeParticipantInfo,
    ChallengeDayProgress,
    ChallengeDetailsResponse,
    ChallengeMyCalendarResponse,
    ChallengeClaimResponse,
)

__all__ = [
    # Common
    "PaginatedResponse",
    # Users
    "UserResponse",
    "UserStatsResponse",
    "UpdateUserRequest",
    "CompleteOnboardingRequest",
    "UserProfileResponse",
    "ExerciseRecord",
    "UserRecordsResponse",
    "DayActivityResponse",
    "UserActivityResponse",
    # Auth
    "AuthRequest",
    "AuthResponse",
    "WebAuthResponse",
    "WebRegisterRequest",
    "WebLoginRequest",
    "SetPasswordRequest",
    "LinkTelegramRequest",
    "ConfirmLinkResponse",
    # Workouts
    "ExerciseSetData",
    "CompleteWorkoutRequest",
    "WorkoutExerciseResponse",
    "WorkoutResponse",
    "WorkoutSummaryResponse",
    "TodayStatsResponse",
    # Exercises
    "CategoryResponse",
    "ExerciseResponse",
    "ExerciseProgressResponse",
    "ExerciseWithProgressResponse",
    "RoutineExerciseResponse",
    "RoutineResponse",
    "FavoriteResponse",
    # Goals
    "CreateGoalRequest",
    "GoalResponse",
    # Friends
    "FriendResponse",
    "AddFriendRequest",
    # Achievements
    "AchievementResponse",
    "RecentAchievementResponse",
    # Leaderboard
    "LeaderboardEntry",
    "LeaderboardResponse",
    # Shop
    "ShopItemResponse",
    "InventoryItemResponse",
    # Notifications
    "NotificationResponse",
    "UnreadCountResponse",
    # Custom Routines
    "RoutineExerciseCreate",
    "RoutineExerciseResponse",
    "CustomRoutineCreate",
    "CustomRoutineUpdate",
    "CustomRoutineResponse",
    "CustomRoutineListItem",
    # Boss
    "BossResponse",
    "BossLeaderboardEntry",
    "BossLeaderboardResponse",
    "BossMyContributionResponse",
    "BossClaimResponse",
    "BossHistoryEntry",
    "BossHistoryResponse",
    # Challenges
    "ChallengeExerciseCreate",
    "ChallengeCreate",
    "ChallengeExerciseResponse",
    "ChallengeListItem",
    "ChallengeParticipantInfo",
    "ChallengeDayProgress",
    "ChallengeDetailsResponse",
    "ChallengeMyCalendarResponse",
    "ChallengeClaimResponse",
]
