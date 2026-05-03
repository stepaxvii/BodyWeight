"""Monthly boss schemas."""
from datetime import date, datetime
from pydantic import BaseModel


class BossResponse(BaseModel):
    id: int
    slug: str
    name_ru: str
    image_emoji: str
    image_url: str | None = None
    theme: str
    legend_ru: str
    max_hp: int
    current_hp: int
    start_date: date
    end_date: date
    status: str  # 'active' | 'defeated' | 'expired'
    defeated_at: datetime | None = None
    finalized_at: datetime | None = None

    class Config:
        from_attributes = True


class BossLeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str | None
    first_name: str | None
    avatar_id: str | None
    total_damage: int
    attacks_count: int


class BossLeaderboardResponse(BaseModel):
    boss_id: int
    entries: list[BossLeaderboardEntry]


class BossMyContributionResponse(BaseModel):
    boss_id: int
    rank: int | None
    total_damage: int
    attacks_count: int
    last_attack_at: datetime | None
    reward_tier: str | None
    reward_coins: int
    is_top10: bool
    reward_claimable: bool  # finalized + not yet claimed + within TTL
    reward_claimed_at: datetime | None


class BossClaimResponse(BaseModel):
    coins_awarded: int


class BossHistoryEntry(BaseModel):
    id: int
    name_ru: str
    image_emoji: str
    image_url: str | None = None
    theme: str
    start_date: date
    end_date: date
    status: str
    my_total_damage: int
    my_rank: int | None
    my_reward_coins: int
    my_reward_claimed: bool


class BossHistoryResponse(BaseModel):
    bosses: list[BossHistoryEntry]
