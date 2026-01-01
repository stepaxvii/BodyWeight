"""Achievement-related Pydantic schemas."""

from pydantic import BaseModel


class AchievementResponse(BaseModel):
    """Achievement response schema."""
    slug: str
    name: str
    name_ru: str
    description: str
    description_ru: str
    icon: str
    xp_reward: int
    coin_reward: int
    unlocked: bool
    unlocked_at: str | None = None
    condition: dict


class RecentAchievementResponse(BaseModel):
    """Recent achievement response schema."""
    slug: str
    name: str
    name_ru: str
    icon: str
    unlocked_at: str
