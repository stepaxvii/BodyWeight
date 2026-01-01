"""Leaderboard-related Pydantic schemas."""

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    """Leaderboard entry schema."""
    rank: int
    user_id: int
    username: str | None
    first_name: str | None
    avatar_id: str
    level: int
    total_xp: int
    current_streak: int
    is_current_user: bool = False


class LeaderboardResponse(BaseModel):
    """Leaderboard response schema."""
    entries: list[LeaderboardEntry]
    current_user_rank: int | None = None
