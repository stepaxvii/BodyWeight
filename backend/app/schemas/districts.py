"""RPG districts & quests schemas.

Bilingual inline content (decision 1): the unsuffixed field is English, the
`*_ru` field is Russian (rendered by the client via `ln(en, ru)`). These mirror
the raw `districts.json` content served by `services.districts` plus the live,
per-player quest state computed on the fly.

The content shapes are intentionally permissive — the service returns the raw
JSON dicts with a couple of derived keys spliced in (`status`, `quest_progress`)
— so the response models use defaulted optional fields and let unknown stub
keys (e.g. the TBD `quest._status`) be dropped by Pydantic.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Content sub-models (static, from districts.json)
# ---------------------------------------------------------------------------

class DistrictBoss(BaseModel):
    model_config = ConfigDict(extra="ignore")

    avatar: str | None = None
    name: str | None = None
    name_ru: str | None = None
    role: str | None = None
    role_ru: str | None = None


class QuestExercise(BaseModel):
    model_config = ConfigDict(extra="ignore")

    exercise_slug: str
    equipment: str | None = None
    daily_target: int


class QuestReward(BaseModel):
    model_config = ConfigDict(extra="ignore")

    xp: int = 0
    coins: int = 0
    title_slug: str | None = None
    title: str | None = None
    title_ru: str | None = None


class Quest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    district_id: str | None = None
    title: str | None = None
    title_ru: str | None = None
    days: int | None = None
    per_day_all: bool | None = None
    exercises: list[QuestExercise] = []
    reward: QuestReward | None = None
    unlocks: list[str] = []


# ---------------------------------------------------------------------------
# Live per-player quest progress (computed, not persisted)
# ---------------------------------------------------------------------------

class QuestProgressExercise(BaseModel):
    exercise_slug: str
    name: str | None = None
    name_ru: str | None = None
    daily_target: int
    accumulated: int
    completed: bool
    is_timed: bool


class QuestProgress(BaseModel):
    """Light summary (list view) or full per-exercise tally (detail view)."""
    model_config = ConfigDict(extra="ignore")

    challenge_id: int
    challenge_status: str
    full_days: int
    days: int
    start_date: str
    end_date: str
    mercenary_avatar: str | None = None
    # Present only on the detail endpoint's live progress.
    exercises: list[QuestProgressExercise] | None = None


# ---------------------------------------------------------------------------
# Incoming co-op invite (computed, per current user, per district)
# ---------------------------------------------------------------------------

class IncomingInvite(BaseModel):
    """A pending co-op invite the CURRENT user has on this district's quest.

    Set when the user has a ChallengeParticipant row with invite_status='pending'
    on a quest challenge whose quest belongs to this district. `inviter_name` is
    the display name of the instance's inviter (the NULL-invite_status creator).
    Null otherwise.
    """
    model_config = ConfigDict(extra="ignore")

    inviter_name: str
    inviter_user_id: int
    challenge_id: int
    quest_title: str
    quest_title_ru: str


# ---------------------------------------------------------------------------
# District responses
# ---------------------------------------------------------------------------

class DistrictResponse(BaseModel):
    """One district: static bilingual content + this player's live status."""
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    name_ru: str
    order: int
    scene: str | None = None
    muscle: str | None = None
    muscle_ru: str | None = None
    boss: DistrictBoss | None = None
    unlock: dict | None = None
    quest: Quest | None = None
    dialogue: dict | None = None
    # Co-op is MANDATORY on a few future districts and absent on the solo ones.
    # Drives whether the client shows any co-op/mercenary UI (default: solo).
    coop: bool = False

    # Derived, per-player.
    status: str  # locked | available | active | completed
    quest_progress: QuestProgress | None = None
    # A pending co-op invite the current user has on this district (or null).
    incoming_invite: IncomingInvite | None = None


class DistrictListResponse(BaseModel):
    districts: list[DistrictResponse]


# ---------------------------------------------------------------------------
# Action request bodies
# ---------------------------------------------------------------------------

class InvitePartnerRequest(BaseModel):
    user_id: int


class HireMercenaryRequest(BaseModel):
    avatar: str


class AcceptQuestResponse(BaseModel):
    challenge_id: int
    quest_id: str | None = None
    status: str
    start_date: str
    end_date: str
