"""User-created challenge schemas."""
from datetime import date, datetime
from pydantic import BaseModel, Field


# --- Inputs ---------------------------------------------------------------


class ChallengeExerciseCreate(BaseModel):
    exercise_slug: str
    daily_target: int = Field(gt=0)


class ChallengeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    start_date: date
    end_date: date
    exercises: list[ChallengeExerciseCreate] = Field(min_length=1, max_length=5)


# --- Outputs --------------------------------------------------------------


class ChallengeExerciseResponse(BaseModel):
    exercise_id: int
    exercise_slug: str
    exercise_name_ru: str
    daily_target: int
    is_timed: bool
    order_index: int


class ChallengeListItem(BaseModel):
    id: int
    title: str
    creator_user_id: int | None
    creator_name: str | None
    start_date: date
    end_date: date
    status: str
    participants_count: int
    exercises_count: int
    is_member: bool
    total_days: int = 0
    daily_target_total: int = 0  # sum of all exercises' daily targets
    # Personal progress (only for members on active/finished challenges)
    completion_percent: int | None = None
    completed_days: int | None = None
    # Unclaimed reward signal for finished challenges
    reward_claimable: bool = False
    reward_coins: int = 0


class ChallengeParticipantInfo(BaseModel):
    user_id: int
    username: str | None
    first_name: str | None
    avatar_id: str | None
    completion_percent: int  # live (running) or final (after finalization)
    completed_days: int
    reward_tier: str | None
    reward_coins: int
    reward_claimable: bool
    reward_claimed_at: datetime | None


class ChallengeDayProgress(BaseModel):
    """One row per (date, exercise) showing accumulated/target/completed."""
    progress_date: date
    exercise_id: int
    exercise_slug: str
    exercise_name_ru: str
    accumulated: int
    target: int
    completed: bool


class ChallengeDetailsResponse(BaseModel):
    id: int
    title: str
    description: str | None
    creator_user_id: int | None
    creator_name: str | None
    start_date: date
    end_date: date
    duration_days: int
    status: str
    finalized_at: datetime | None
    exercises: list[ChallengeExerciseResponse]
    participants: list[ChallengeParticipantInfo]
    is_member: bool
    can_join: bool


class ChallengeMyCalendarResponse(BaseModel):
    """My personal grid of progress per (date, exercise)."""
    challenge_id: int
    rows: list[ChallengeDayProgress]


class ChallengeClaimResponse(BaseModel):
    coins_awarded: int
