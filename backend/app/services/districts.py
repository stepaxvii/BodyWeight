"""RPG districts & quests — static content loader + validation + mechanics.

`districts.json` is read inline (like `bosses.json`), bilingual via the
unsuffixed-EN / `*_ru` convention. A quest materializes into a `Challenge`
(`quest_id` set) when a player accepts it. This module owns:

- loading / lookup helpers + structural validation (Phase A, unchanged below);
- the Phase-B mechanics: on-the-fly district state, quest accept / abandon,
  the fixed-reward grant, co-op invite state machine and the cosmetic mercenary.

Quest challenges are kept strictly off the ordinary-challenge surface by the 6
isolation seams in services.challenges / api.routes.challenges — this module
only ever touches `quest_id NOT NULL` instances.

Imports from `services.challenges` are done LATE (function-level) because that
module does not import this one today, but the reverse coupling is kept cheap /
cycle-safe by convention.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Challenge,
    ChallengeExercise,
    ChallengeParticipant,
    ChallengeProgress,
    Exercise,
    Friendship,
    ShopItem,
    User,
    UserPurchase,
    UserQuestCompletion,
)
from app.i18n import t
from app.services.notifications import save_notification

logger = logging.getLogger(__name__)

_DATA = Path(__file__).parent.parent / "data" / "districts.json"

# Mirror the challenge-engine limits so a quest can always materialize.
_ALLOWED_EQUIPMENT = {"none", "pullup-bar", "dip-bars"}
_MAX_EXERCISES = 5        # services.challenges.MAX_EXERCISES
_MIN_DAYS, _MAX_DAYS = 3, 365  # services.challenges.MIN/MAX_DURATION_DAYS

# Co-op / mercenary tunables (spec §7.4 / §7.5).
INVITE_TTL_HOURS = 48
MERCENARY_HIRE_COST = 50

# v1 co-op cap: 1 partner / 2 participants total (counting pending invites too).
_MAX_PARTICIPANTS = 2

_cache: dict | None = None


def load_districts() -> dict:
    """Load + cache districts.json (module-global cache, like boss.py)."""
    global _cache
    if _cache is None:
        with open(_DATA, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def districts() -> list[dict]:
    return load_districts()["districts"]


def district_by_id(district_id: str) -> dict | None:
    return next((d for d in districts() if d["id"] == district_id), None)


def quest_by_id(quest_id: str) -> dict | None:
    """Return the quest dict for a quest_id (with its district id attached), or None."""
    for d in districts():
        q = d.get("quest") or {}
        if q.get("id") == quest_id:
            return {**q, "_district_id": d["id"]}
    return None


def playable_quests() -> list[dict]:
    """Quests that have an exercise set (home/french/cossack; not the stubs)."""
    out = []
    for d in districts():
        q = d.get("quest") or {}
        if q.get("exercises"):
            out.append({**q, "_district_id": d["id"]})
    return out


def validate(valid_slugs: set[str]) -> list[str]:
    """Structural validation against the seeded Exercise slug set.

    Returns a list of human-readable problems (empty list == OK). Intended to run
    once at startup (after exercises are seeded) so bad content fails loud rather
    than crashing create_challenge at accept time.
    """
    problems: list[str] = []
    data = load_districts()
    allowed = set(data.get("allowed_equipment_starter", _ALLOWED_EQUIPMENT))
    ids_seen: set[str] = set()
    quest_ids_seen: set[str] = set()

    for d in data["districts"]:
        did = d.get("id")
        if not did:
            problems.append("district without id")
            continue
        if did in ids_seen:
            problems.append(f"duplicate district id {did}")
        ids_seen.add(did)

        q = d.get("quest") or {}
        exercises = q.get("exercises")
        if not exercises:
            continue  # stub district (downtown/port): unlock + locked dialogue only

        qid = q.get("id", f"<{did}>")
        if qid in quest_ids_seen:
            problems.append(f"duplicate quest id {qid}")
        quest_ids_seen.add(qid)

        days = q.get("days", 0)
        if not (_MIN_DAYS <= days <= _MAX_DAYS):
            problems.append(f"{qid}: days {days} out of [{_MIN_DAYS}, {_MAX_DAYS}]")
        if len(exercises) > _MAX_EXERCISES:
            problems.append(f"{qid}: {len(exercises)} exercises > max {_MAX_EXERCISES}")

        for e in exercises:
            slug = e.get("exercise_slug")
            if slug not in valid_slugs:
                problems.append(f"{qid}: unknown exercise_slug '{slug}'")
            eq = e.get("equipment")
            if eq not in allowed:
                problems.append(f"{qid}: '{slug}' equipment '{eq}' not in {sorted(allowed)}")
            easier = e.get("easier")
            if easier and easier not in valid_slugs:
                problems.append(f"{qid}: easier '{easier}' is not a known slug")

    # Note: unlock-ref cross-checking is intentionally NOT done here — the stub
    # districts (downtown/port) legitimately point at not-yet-authored quests.
    return problems


# ===========================================================================
# Phase B — mechanics
# ===========================================================================

# Participant rows that "count" everywhere (lock §4.9, wait-for-all §4.7):
# NULL (solo / inviter) or 'accepted' (friend who said yes). 'pending'/'declined'
# never count. We filter in Python/SQL with this helper predicate.
def _counts_as_active(invite_status: str | None) -> bool:
    return invite_status is None or invite_status == "accepted"


def _active_invite_filter():
    """SQL predicate: ChallengeParticipant rows that count (NULL or 'accepted')."""
    return or_(
        ChallengeParticipant.invite_status.is_(None),
        ChallengeParticipant.invite_status == "accepted",
    )


# ---------------------------------------------------------------------------
# full_days helper (spec §4.1) — the raw AND-day count, service-layer twin of
# the route's _calc_running_completion / challenges._participant_completion_percent.
# ---------------------------------------------------------------------------

async def compute_full_days(
    session: AsyncSession,
    challenge: Challenge,
    user_id: int,
) -> int:
    """Number of DISTINCT calendar dates where ALL of the challenge's exercises
    hit their daily target for this user (AND-per-day). Returns the raw count
    (NOT a percentage), so the quest-completion hook can compare it to days.
    """
    ex_result = await session.execute(
        select(func.count(ChallengeExercise.id)).where(
            ChallengeExercise.challenge_id == challenge.id
        )
    )
    n_exercises = ex_result.scalar() or 0
    if n_exercises == 0:
        return 0

    rows = await session.execute(
        select(ChallengeProgress.progress_date)
        .where(ChallengeProgress.challenge_id == challenge.id)
        .where(ChallengeProgress.user_id == user_id)
        .where(ChallengeProgress.completed.is_(True))
        # Only count days WITHIN the (possibly rewritten) quest window, so a
        # co-op head start (accept_invite moves start_date to today+1) never
        # lets a pre-invite day count toward full_days (spec §4.5).
        .where(ChallengeProgress.progress_date >= challenge.start_date)
        .where(ChallengeProgress.progress_date <= challenge.end_date)
    )
    counts: dict = {}
    for (d,) in rows.all():
        counts[d] = counts.get(d, 0) + 1
    return sum(1 for v in counts.values() if v >= n_exercises)


# ---------------------------------------------------------------------------
# Fixed reward (spec §6) — the ONLY source of a quest's reward. Tiers/claim are
# never applied to quest challenges (that would double-grant coins).
# ---------------------------------------------------------------------------

async def apply_quest_reward(session: AsyncSession, user: User, quest: dict) -> None:
    """Grant the quest's FIXED reward to `user`: XP (+ level recompute), coins,
    and title ownership (idempotent UserPurchase). No reward tiers, no claim.

    `quest` is a quest dict from districts.json (with its `reward` sub-dict).
    Caller is responsible for persisting (same txn as the UserQuestCompletion).
    """
    from app.services.xp_calculator import get_level_from_xp

    reward = quest.get("reward") or {}

    xp = int(reward.get("xp", 0) or 0)
    coins = int(reward.get("coins", 0) or 0)

    # XP + mandatory level recompute (do NOT copy the achievement_checker bug
    # that leaves user.level stale until the next workout).
    if xp:
        user.total_xp += xp
    user.level = get_level_from_xp(user.total_xp)

    # Coins — flat, no per-level bonus (fixed-reward decision, §6 p.3).
    if coins:
        user.coins += coins

    # Title ownership via a UserPurchase row (not via the shop route, so no coin
    # deduction). Idempotent against uq_user_purchase.
    title_slug = reward.get("title_slug")
    if title_slug:
        item = (
            await session.execute(
                select(ShopItem).where(ShopItem.slug == title_slug)
            )
        ).scalar_one_or_none()
        if item is not None:
            owned = (
                await session.execute(
                    select(UserPurchase.id).where(
                        UserPurchase.user_id == user.id,
                        UserPurchase.shop_item_id == item.id,
                    )
                )
            ).scalar_one_or_none()
            if owned is None:
                session.add(
                    UserPurchase(
                        user_id=user.id,
                        shop_item_id=item.id,
                        is_equipped=False,
                    )
                )
        else:
            logger.warning(
                "Quest %s reward title '%s' has no ShopItem — title not granted",
                quest.get("id"),
                title_slug,
            )

    await session.flush()


# ---------------------------------------------------------------------------
# Completion lookups
# ---------------------------------------------------------------------------

async def _completed_quest_ids(session: AsyncSession, user_id: int) -> set[str]:
    rows = await session.execute(
        select(UserQuestCompletion.quest_id).where(
            UserQuestCompletion.user_id == user_id
        )
    )
    return {q for (q,) in rows.all()}


async def _has_completed(session: AsyncSession, user_id: int, quest_id: str) -> bool:
    found = (
        await session.execute(
            select(UserQuestCompletion.id).where(
                UserQuestCompletion.user_id == user_id,
                UserQuestCompletion.quest_id == quest_id,
            )
        )
    ).scalar_one_or_none()
    return found is not None


async def _active_quest_challenge(
    session: AsyncSession,
    user_id: int,
    quest_id: str,
) -> Challenge | None:
    """The user's live (upcoming/active) quest-Challenge instance for a given
    quest_id where they are a counting participant (invite_status NULL/accepted)
    and have NOT personally completed it yet. None if there is none.
    """
    if await _has_completed(session, user_id, quest_id):
        return None
    result = await session.execute(
        select(Challenge)
        .join(ChallengeParticipant, ChallengeParticipant.challenge_id == Challenge.id)
        .where(ChallengeParticipant.user_id == user_id)
        .where(_active_invite_filter())
        .where(Challenge.quest_id == quest_id)
        .where(Challenge.status.in_(["upcoming", "active"]))
        .order_by(Challenge.id.desc())
    )
    return result.scalars().first()


async def _incoming_invite(
    session: AsyncSession,
    user_id: int,
    quest: dict,
) -> dict | None:
    """The CURRENT user's pending co-op invite for a given quest, or None.

    Returns the CONTRACT shape (inviter_name / inviter_user_id / challenge_id /
    quest_title / quest_title_ru) when the user has a ChallengeParticipant row
    with invite_status='pending' on a live (upcoming/active) quest-Challenge for
    `quest`. inviter_name is the display name of the instance's inviter (the
    participant with invite_status NULL, i.e. the creator). None otherwise.
    """
    quest_id = quest.get("id")
    if not quest_id:
        return None

    # The user's pending invite row + its challenge.
    row = (
        await session.execute(
            select(ChallengeParticipant.challenge_id)
            .join(Challenge, Challenge.id == ChallengeParticipant.challenge_id)
            .where(ChallengeParticipant.user_id == user_id)
            .where(ChallengeParticipant.invite_status == "pending")
            .where(Challenge.quest_id == quest_id)
            .where(Challenge.status.in_(["upcoming", "active"]))
            .order_by(Challenge.id.desc())
        )
    ).first()
    if row is None:
        return None
    challenge_id = row[0]

    # Resolve the inviter = the NULL-invite_status participant (creator) of the
    # same instance, joined to their User for the display name.
    inviter = (
        await session.execute(
            select(User)
            .join(
                ChallengeParticipant,
                ChallengeParticipant.user_id == User.id,
            )
            .where(ChallengeParticipant.challenge_id == challenge_id)
            .where(ChallengeParticipant.invite_status.is_(None))
            .order_by(ChallengeParticipant.id.asc())
        )
    ).scalars().first()
    if inviter is None:
        return None

    inviter_name = _display_name(inviter) if inviter else ""
    return {
        "inviter_name": inviter_name,
        "inviter_user_id": inviter.id,
        "challenge_id": challenge_id,
        "quest_title": quest.get("title") or quest_id,
        "quest_title_ru": quest.get("title_ru") or quest.get("title") or quest_id,
    }


async def _locking_quest(session: AsyncSession, user: User) -> Challenge | None:
    """The user's current one-active-quest lock holder, or None (spec §4.9/§5).

    Counts ONLY quest challenges where the user is a NULL/accepted participant,
    the instance is upcoming/active, and the user has no UserQuestCompletion for
    that quest_id yet. Ordinary challenges (quest_id NULL) never lock.
    """
    completed = await _completed_quest_ids(session, user.id)
    result = await session.execute(
        select(Challenge)
        .join(ChallengeParticipant, ChallengeParticipant.challenge_id == Challenge.id)
        .where(ChallengeParticipant.user_id == user.id)
        .where(_active_invite_filter())
        .where(Challenge.quest_id.isnot(None))
        .where(Challenge.status.in_(["upcoming", "active"]))
    )
    for ch in result.scalars().all():
        if ch.quest_id not in completed:
            return ch
    return None


# ---------------------------------------------------------------------------
# District state (spec §2.4 / §4) — derived on the fly, never persisted.
# ---------------------------------------------------------------------------

def _unlock_satisfied(unlock: dict, completed: set[str]) -> bool:
    utype = (unlock or {}).get("type")
    if utype == "start":
        return True
    if utype == "quest_done":
        return unlock.get("quest") in completed
    if utype == "all_of":
        return all(q in completed for q in (unlock.get("quests") or []))
    return False  # unknown / stub unlock => locked


async def compute_state(session: AsyncSession, user: User) -> list[dict]:
    """All districts + this player's per-district status, computed on the fly.

    status ∈ {locked, available, active, completed}:
      - completed : the district's quest is in UserQuestCompletion
      - active    : a live (upcoming/active) quest-Challenge exists for it
      - available : unlock rule satisfied, no completion/active instance
      - locked    : unlock rule not satisfied (or stub without a playable quest)

    Returns one dict per district with the raw bilingual content plus `status`
    and (when active) a light `quest_progress` summary. The route serializes it.
    """
    completed = await _completed_quest_ids(session, user.id)
    out: list[dict] = []
    for d in districts():
        quest = d.get("quest") or {}
        quest_id = quest.get("id")
        playable = bool(quest.get("exercises"))
        unlocked = _unlock_satisfied(d.get("unlock") or {}, completed)

        status = "locked"
        quest_progress: dict | None = None
        if not unlocked or not playable:
            status = "locked"
        elif quest_id in completed:
            status = "completed"
        else:
            ch = await _active_quest_challenge(session, user.id, quest_id)
            if ch is not None:
                status = "active"
                full_days = await compute_full_days(session, ch, user.id)
                quest_progress = {
                    "challenge_id": ch.id,
                    "full_days": full_days,
                    "days": int(quest.get("days", 0) or 0),
                    "start_date": ch.start_date.isoformat(),
                    "end_date": ch.end_date.isoformat(),
                    "challenge_status": ch.status,
                    "mercenary_avatar": ch.mercenary_avatar,
                }
            else:
                status = "available"

        # Pending co-op invite the current user has on this district (or None),
        # independent of the derived status (a pending invitee still sees the
        # district as 'available' until they accept — spec §4.9/§7).
        incoming_invite = None
        if playable:
            incoming_invite = await _incoming_invite(session, user.id, quest)

        out.append(
            {
                **d,
                "status": status,
                "quest_progress": quest_progress,
                "incoming_invite": incoming_invite,
            }
        )
    return out


async def get_detail(session: AsyncSession, user: User, district_id: str) -> dict:
    """One district: full bilingual content + live quest progress (if active).

    Raises ValueError (→400) on unknown district.
    """
    d = district_by_id(district_id)
    if d is None:
        raise ValueError("Unknown district")

    completed = await _completed_quest_ids(session, user.id)
    quest = d.get("quest") or {}
    quest_id = quest.get("id")
    playable = bool(quest.get("exercises"))
    unlocked = _unlock_satisfied(d.get("unlock") or {}, completed)

    status = "locked"
    quest_progress: dict | None = None
    if unlocked and playable:
        if quest_id in completed:
            status = "completed"
        else:
            ch = await _active_quest_challenge(session, user.id, quest_id)
            if ch is not None:
                status = "active"
                quest_progress = await _live_quest_progress(session, user, ch, quest)
            else:
                status = "available"

    incoming_invite = None
    if playable:
        incoming_invite = await _incoming_invite(session, user.id, quest)

    return {
        **d,
        "status": status,
        "quest_progress": quest_progress,
        "incoming_invite": incoming_invite,
    }


async def _live_quest_progress(
    session: AsyncSession,
    user: User,
    challenge: Challenge,
    quest: dict,
) -> dict:
    """Per-exercise live tally for an active quest instance (today's rows)."""
    today = datetime.utcnow().date()
    full_days = await compute_full_days(session, challenge, user.id)

    # Per-exercise meta for the quest, keyed by exercise_id (<=5 rows).
    rows = await session.execute(
        select(
            Exercise.id,
            Exercise.slug,
            Exercise.name,
            Exercise.name_ru,
            ChallengeExercise.daily_target,
            ChallengeExercise.is_timed,
            ChallengeExercise.order_index,
        )
        .join(ChallengeExercise, ChallengeExercise.exercise_id == Exercise.id)
        .where(ChallengeExercise.challenge_id == challenge.id)
        .order_by(ChallengeExercise.order_index)
    )
    ex_meta = rows.all()

    # Today's progress rows for this user on this challenge, keyed by exercise_id.
    prog_rows = await session.execute(
        select(ChallengeProgress.exercise_id, ChallengeProgress.accumulated)
        .where(ChallengeProgress.challenge_id == challenge.id)
        .where(ChallengeProgress.user_id == user.id)
        .where(ChallengeProgress.progress_date == today)
    )
    acc_by_ex_id = {ex_id: acc for ex_id, acc in prog_rows.all()}

    exercises = []
    for ex_id, slug, name, name_ru, target, is_timed, _order in ex_meta:
        accumulated = acc_by_ex_id.get(ex_id, 0)
        exercises.append(
            {
                "exercise_slug": slug,
                "name": name,
                "name_ru": name_ru,
                "daily_target": target,
                "accumulated": accumulated,
                "completed": accumulated >= target,
                "is_timed": bool(is_timed),
            }
        )

    return {
        "challenge_id": challenge.id,
        "challenge_status": challenge.status,
        "full_days": full_days,
        "days": int(quest.get("days", 0) or 0),
        "start_date": challenge.start_date.isoformat(),
        "end_date": challenge.end_date.isoformat(),
        "mercenary_avatar": challenge.mercenary_avatar,
        "exercises": exercises,
    }


# ---------------------------------------------------------------------------
# Accept / abandon (spec §4.2 / §4.10)
# ---------------------------------------------------------------------------

# Quest reps scale with the player's level so a seasoned fighter gets a
# commensurate challenge instead of a trivial one. Gentle linear ramp of +5% per
# level above 1, capped at 2x the authored base (reached at level ~21). The base
# daily_target in districts.json is therefore the level-1 (beginner) target.
_QUEST_SCALE_PER_LEVEL = 0.05
_QUEST_SCALE_CAP = 2.0


def scale_target_for_level(base: int, level: int) -> int:
    """Scale a quest's base daily_target up for a higher-level player.

    Never below the base; capped at 2x. Co-op quests (none yet) are expected to
    pass the AVERAGE level of the participating players.
    """
    factor = min(_QUEST_SCALE_CAP, 1.0 + max(0, level - 1) * _QUEST_SCALE_PER_LEVEL)
    return max(int(base), round(int(base) * factor))


async def accept_quest(session: AsyncSession, user: User, district_id: str) -> Challenge:
    """Materialize the district's quest into a Challenge (quest_id set) and add
    the player as the inviter/solo participant (invite_status=NULL).

    SOLO window: today is a prep day — start_date=tomorrow,
    end_date=tomorrow+days-1 → status='upcoming', auto-advancing to 'active' on the
    start date (the boss says "завтра жду тебя на тренировку"). Quest rep targets
    are scaled to the player's level (see ``scale_target_for_level``). Enforces the
    one-active-quest lock (spec §4.9/§5). Raises ValueError (→400).
    """
    from app.services.challenges import (
        CreateChallengeInput,
        ChallengeExerciseInput,
        create_challenge,
    )
    from app.services.xp_calculator import get_level_from_xp

    d = district_by_id(district_id)
    if d is None:
        raise ValueError("Unknown district")

    quest = d.get("quest") or {}
    quest_id = quest.get("id")
    exercises = quest.get("exercises") or []
    if not quest_id or not exercises:
        raise ValueError("District has no playable quest")

    completed = await _completed_quest_ids(session, user.id)

    # District must be available (unlock satisfied, not already completed).
    if not _unlock_satisfied(d.get("unlock") or {}, completed):
        raise ValueError("District is locked")
    if quest_id in completed:
        raise ValueError("Quest already completed")

    # One active quest at a time (counts only quest challenges w/o personal
    # completion where the user is a NULL/accepted participant).
    if await _locking_quest(session, user) is not None:
        raise ValueError("You already have an active quest")

    days = int(quest.get("days", 0) or 0)
    today = datetime.utcnow().date()
    # The quest counts from TOMORROW (today is a prep day — the boss says "завтра
    # жду тебя на тренировку"): window = [tomorrow .. tomorrow+days-1]. The challenge
    # starts 'upcoming' and flips to 'active' automatically when the date arrives.
    start = today + timedelta(days=1)
    # Scale rep targets to the player's current level (from XP, so a stale
    # user.level doesn't matter).
    level = get_level_from_xp(user.total_xp)
    data = CreateChallengeInput(
        title=quest.get("title") or quest_id,
        description=None,
        start_date=start,
        end_date=start + timedelta(days=days - 1),
        exercises=[
            ChallengeExerciseInput(
                exercise_slug=e["exercise_slug"],
                daily_target=scale_target_for_level(int(e["daily_target"]), level),
            )
            for e in exercises
        ],
    )

    challenge = await create_challenge(session, creator=user, data=data)
    # Mark it a quest AFTER creation (create_challenge is quest-unaware).
    challenge.quest_id = quest_id
    # Creator is the inviter / solo participant: invite_status NULL (create_challenge
    # already added the participant row with the default NULL invite_status).
    await session.flush()
    return challenge


async def _find_district_quest_challenge(
    session: AsyncSession,
    user: User,
    district_id: str,
) -> tuple[dict, dict, Challenge | None]:
    """Resolve (district, quest, live_challenge) for a player action on a
    district. Raises ValueError on unknown district / no playable quest.
    """
    d = district_by_id(district_id)
    if d is None:
        raise ValueError("Unknown district")
    quest = d.get("quest") or {}
    quest_id = quest.get("id")
    if not quest_id or not quest.get("exercises"):
        raise ValueError("District has no playable quest")
    ch = await _active_quest_challenge(session, user.id, quest_id)
    return d, quest, ch


async def abandon_quest(session: AsyncSession, user: User, district_id: str) -> None:
    """Abandon the player's active quest in a district (spec §4.10).

    Solo: delete the whole instance (cascade clears exercises/participants/
    progress). Co-op: remove only this player's participant row; if no counting
    participants remain, close/delete the instance. Mercenary coins are NOT
    refunded. Raises ValueError (→400) if there is no active quest.
    """
    _d, _quest, ch = await _find_district_quest_challenge(session, user, district_id)
    if ch is None:
        raise ValueError("No active quest in this district")

    # Load all participants of the instance.
    result = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == ch.id
        )
    )
    participants = list(result.scalars().all())

    mine = next((p for p in participants if p.user_id == user.id), None)
    if mine is None:
        raise ValueError("Not a participant of this quest")

    # Remaining COUNTING participants (NULL/accepted) other than me.
    others_counting = [
        p
        for p in participants
        if p.user_id != user.id and _counts_as_active(p.invite_status)
    ]

    if others_counting:
        # Co-op with surviving partners: drop only my row; also clear my
        # progress rows for this challenge so stale tallies don't linger.
        await session.delete(mine)
        await session.execute(
            ChallengeProgress.__table__.delete().where(
                (ChallengeProgress.challenge_id == ch.id)
                & (ChallengeProgress.user_id == user.id)
            )
        )
    else:
        # Solo, or I'm the last real participant — delete the whole instance
        # (cascade clears exercises / participants / progress / mercenary).
        await session.delete(ch)

    await session.flush()


# ---------------------------------------------------------------------------
# Co-op invite state machine (spec §7)
# ---------------------------------------------------------------------------

@dataclass
class QuestInvitePush:
    """A best-effort Telegram push the ROUTE should fire AFTER committing.

    The in-app bell notification is already written (save_notification) inside
    the same transaction as the state change; this descriptor only carries what
    the post-commit push wrapper needs. `kind` selects the send_* wrapper.
    telegram_id is None when the recipient opted out / has no chat — the route
    simply skips the push then.
    """
    kind: str  # 'received' | 'accepted' | 'declined'
    telegram_id: int | None
    lang: str
    quest_challenge_id: int
    # received: inviter is the actor, quest+district shown; name = inviter's name
    # accepted/declined: partner is the actor; name = partner's name
    actor_name: str
    quest_title: str
    quest_title_ru: str
    district_name: str
    district_name_ru: str


def _display_name(u: User) -> str:
    return u.username or u.first_name or t(u.language, "bot.common.user_fallback")

async def _is_accepted_friend(session: AsyncSession, user: User, friend_user_id: int) -> bool:
    """True if friend_user_id is an accepted friend of `user` (bidirectional,
    mirrors notify_friends_new_challenge's resolver — tolerant of one edge).
    """
    found = (
        await session.execute(
            select(Friendship.id)
            .where(
                or_(
                    and_(
                        Friendship.user_id == user.id,
                        Friendship.friend_id == friend_user_id,
                    ),
                    and_(
                        Friendship.friend_id == user.id,
                        Friendship.user_id == friend_user_id,
                    ),
                )
            )
            .where(Friendship.status == "accepted")
        )
    ).first()
    return found is not None


async def _prune_expired_invites(session: AsyncSession, challenge_id: int) -> None:
    """Lazy TTL cleanup: delete 'pending' invite rows older than INVITE_TTL_HOURS
    (spec §7.4). Called opportunistically on invite/accept/decline/detail paths.
    """
    cutoff = datetime.utcnow() - timedelta(hours=INVITE_TTL_HOURS)
    result = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id,
            ChallengeParticipant.invite_status == "pending",
            ChallengeParticipant.joined_at < cutoff,
        )
    )
    for p in result.scalars().all():
        await session.delete(p)


async def invite_partner(
    session: AsyncSession,
    user: User,
    district_id: str,
    friend_user_id: int,
) -> QuestInvitePush | None:
    """Invite an accepted friend to the player's active quest in a district
    (spec §7.3 p.2): insert a 'pending' ChallengeParticipant for the friend.

    Guards: caller owns the quest instance; target is an accepted friend; the
    2-participant cap is not exceeded (counting pending rows). Idempotent per
    uq_challenge_participant; a prior 'declined' row is re-armed to 'pending'.
    Raises ValueError (→400).

    Notifies the INVITEE: writes the in-app bell row (quest.invite.received) in
    THIS transaction and returns a QuestInvitePush so the route can fire the
    best-effort Telegram push AFTER commit. Returns None when the invite was a
    no-op (friend already pending/accepted/a participant) — nothing to notify.
    """
    d, quest, ch = await _find_district_quest_challenge(session, user, district_id)
    if ch is None:
        raise ValueError("No active quest in this district")
    if friend_user_id == user.id:
        raise ValueError("You cannot invite yourself")
    if not await _is_accepted_friend(session, user, friend_user_id):
        raise ValueError("User is not an accepted friend")

    await _prune_expired_invites(session, ch.id)

    # Load current participant rows.
    result = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == ch.id
        )
    )
    participants = list(result.scalars().all())

    # Idempotency: existing row for this friend.
    existing = next((p for p in participants if p.user_id == friend_user_id), None)
    if existing is not None:
        if existing.invite_status == "declined":
            existing.invite_status = "pending"
            existing.joined_at = datetime.utcnow()
            await session.flush()
            return await _notify_invite_received(session, user, d, quest, ch, friend_user_id)
        # pending/accepted/NULL: short-circuit, nothing to do.
        return None

    # Cap: count NULL/accepted/pending rows (not declined). A declined row would
    # have been handled above; count everything still alive.
    alive = [p for p in participants if p.invite_status != "declined"]
    if len(alive) >= _MAX_PARTICIPANTS:
        raise ValueError("Quest party is full")

    session.add(
        ChallengeParticipant(
            challenge_id=ch.id,
            user_id=friend_user_id,
            invite_status="pending",
        )
    )
    await session.flush()
    return await _notify_invite_received(session, user, d, quest, ch, friend_user_id)


async def _notify_invite_received(
    session: AsyncSession,
    inviter: User,
    district: dict,
    quest: dict,
    challenge: Challenge,
    invitee_user_id: int,
) -> QuestInvitePush | None:
    """Write the invitee's in-app 'invite received' bell row (this txn) and build
    the post-commit push descriptor. Best-effort: a missing invitee just skips."""
    invitee = await session.get(User, invitee_user_id)
    if invitee is None:
        return None

    inviter_name = _display_name(inviter)
    district_name = district.get("name") or district.get("id") or ""
    district_name_ru = district.get("name_ru") or district_name
    quest_title = quest.get("title") or quest.get("id") or ""
    quest_title_ru = quest.get("title_ru") or quest_title
    # Localize the in-app row in the INVITEE's language; pick the matching-language
    # district/quest name for the body (EN default, RU for ru recipients).
    is_ru = (invitee.language or "en").startswith("ru")
    body_district = district_name_ru if is_ru else district_name
    body_quest = quest_title_ru if is_ru else quest_title

    await save_notification(
        session=session,
        user_id=invitee.id,
        notification_type="quest_invite_received",
        title=t(invitee.language, "quest.invite.received.title"),
        message=t(
            invitee.language,
            "quest.invite.received.message",
            from_user_name=inviter_name,
            quest_title=body_quest,
            district_name=body_district,
        ),
        related_user_id=inviter.id,
    )

    telegram_id = invitee.telegram_id if invitee.notifications_enabled else None
    return QuestInvitePush(
        kind="received",
        telegram_id=telegram_id,
        lang=invitee.language or "en",
        quest_challenge_id=challenge.id,
        actor_name=inviter_name,
        quest_title=quest_title,
        quest_title_ru=quest_title_ru,
        district_name=district_name,
        district_name_ru=district_name_ru,
    )


async def _inviter_user(session: AsyncSession, challenge_id: int) -> User | None:
    """The instance's inviter = its NULL-invite_status participant (the creator)."""
    return (
        await session.execute(
            select(User)
            .join(ChallengeParticipant, ChallengeParticipant.user_id == User.id)
            .where(ChallengeParticipant.challenge_id == challenge_id)
            .where(ChallengeParticipant.invite_status.is_(None))
            .order_by(ChallengeParticipant.id.asc())
        )
    ).scalars().first()


async def _notify_invite_answered(
    session: AsyncSession,
    partner: User,
    district: dict,
    quest: dict,
    challenge: Challenge,
    kind: str,  # 'accepted' | 'declined'
) -> QuestInvitePush | None:
    """Write the INVITER's in-app bell row (quest.invite.<kind>) in this txn and
    build the post-commit push descriptor. Best-effort: no inviter → skip."""
    inviter = await _inviter_user(session, challenge.id)
    if inviter is None:
        return None

    partner_name = _display_name(partner)
    district_name = district.get("name") or district.get("id") or ""
    district_name_ru = district.get("name_ru") or district_name
    quest_title = quest.get("title") or quest.get("id") or ""
    quest_title_ru = quest.get("title_ru") or quest_title
    is_ru = (inviter.language or "en").startswith("ru")
    body_quest = quest_title_ru if is_ru else quest_title

    await save_notification(
        session=session,
        user_id=inviter.id,
        notification_type=f"quest_invite_{kind}",
        title=t(inviter.language, f"quest.invite.{kind}.title"),
        message=t(
            inviter.language,
            f"quest.invite.{kind}.message",
            partner_name=partner_name,
            quest_title=body_quest,
        ),
        related_user_id=partner.id,
    )

    telegram_id = inviter.telegram_id if inviter.notifications_enabled else None
    return QuestInvitePush(
        kind=kind,
        telegram_id=telegram_id,
        lang=inviter.language or "en",
        quest_challenge_id=challenge.id,
        actor_name=partner_name,
        quest_title=quest_title,
        quest_title_ru=quest_title_ru,
        district_name=district_name,
        district_name_ru=district_name_ru,
    )


async def accept_invite(
    session: AsyncSession, user: User, district_id: str
) -> QuestInvitePush | None:
    """The invited friend accepts a pending co-op invite (spec §7.3).

    pending→accepted, consumes the friend's one-active-quest lock, and REWRITES
    the shared window: start_date = today+1, end_date = start + days-1, so both
    share one N-day window with no head start. Raises ValueError (→400).

    Notifies the INVITER (quest.invite.accepted) in this txn and returns a
    QuestInvitePush for the route's post-commit best-effort push.
    """
    d = district_by_id(district_id)
    if d is None:
        raise ValueError("Unknown district")
    quest = d.get("quest") or {}
    quest_id = quest.get("id")
    if not quest_id or not quest.get("exercises"):
        raise ValueError("District has no playable quest")

    # Find the user's pending invite row for an instance of this quest.
    result = await session.execute(
        select(ChallengeParticipant, Challenge)
        .join(Challenge, Challenge.id == ChallengeParticipant.challenge_id)
        .where(ChallengeParticipant.user_id == user.id)
        .where(ChallengeParticipant.invite_status == "pending")
        .where(Challenge.quest_id == quest_id)
        .where(Challenge.status.in_(["upcoming", "active"]))
        .order_by(Challenge.id.desc())
    )
    row = result.first()
    if row is None:
        raise ValueError("No pending invite for this quest")
    participant, challenge = row

    # TTL: if the invite has expired, treat it as dead.
    if participant.joined_at is not None:
        if datetime.utcnow() - participant.joined_at > timedelta(hours=INVITE_TTL_HOURS):
            await session.delete(participant)
            await session.flush()
            raise ValueError("Invite expired")

    # Accept consumes the friend's lock (spec §4.9) — reject if they already
    # have another active quest.
    if await _locking_quest(session, user) is not None:
        raise ValueError("You already have an active quest")

    participant.invite_status = "accepted"

    # Rewrite the shared window so both start together tomorrow.
    days = int(quest.get("days", 0) or 0)
    acceptance_date = datetime.utcnow().date()
    challenge.start_date = acceptance_date + timedelta(days=1)
    challenge.end_date = challenge.start_date + timedelta(days=days - 1)
    # status stays 'upcoming' (start_date > today); generic update_challenge_status
    # flips it to 'active' when start_date arrives.
    challenge.status = "upcoming"

    await session.flush()
    return await _notify_invite_answered(session, user, d, quest, challenge, "accepted")


async def decline_invite(
    session: AsyncSession, user: User, district_id: str
) -> QuestInvitePush | None:
    """The invited friend declines a pending co-op invite (spec §7.4): delete the
    pending row. The instance stays a solo quest for the inviter. Raises
    ValueError (→400) if there is no pending invite.

    Notifies the INVITER (quest.invite.declined) in this txn and returns a
    QuestInvitePush for the route's post-commit best-effort push.
    """
    d = district_by_id(district_id)
    if d is None:
        raise ValueError("Unknown district")
    quest = d.get("quest") or {}
    quest_id = quest.get("id")
    if not quest_id:
        raise ValueError("District has no playable quest")

    result = await session.execute(
        select(ChallengeParticipant, Challenge)
        .join(Challenge, Challenge.id == ChallengeParticipant.challenge_id)
        .where(ChallengeParticipant.user_id == user.id)
        .where(ChallengeParticipant.invite_status == "pending")
        .where(Challenge.quest_id == quest_id)
        .order_by(Challenge.id.desc())
    )
    row = result.first()
    if row is None:
        raise ValueError("No pending invite for this quest")
    participant, challenge = row

    # Notify the inviter BEFORE deleting the pending row (we still need the
    # challenge + its inviter participant resolvable). Delete the row so
    # uq_challenge_participant doesn't block a re-invite and the party cap frees
    # up (spec §7.4 recommendation).
    push = await _notify_invite_answered(session, user, d, quest, challenge, "declined")
    await session.delete(participant)
    await session.flush()
    return push


# ---------------------------------------------------------------------------
# Mercenary (spec §7.5) — cosmetic companion, mirrors buy_streak_freeze.
# ---------------------------------------------------------------------------

async def hire_mercenary(
    session: AsyncSession,
    user: User,
    district_id: str,
    avatar: str,
) -> None:
    """Hire a cosmetic mercenary for the player's active quest in a district.

    Funds-check → deduct MERCENARY_HIRE_COST → set challenge.mercenary_avatar →
    flush (mirror of buy_streak_freeze). No ChallengeParticipant, no progress, no
    reward — purely render-only, never gates wait-for-all or the lock. Raises
    ValueError (→400).
    """
    _d, _quest, ch = await _find_district_quest_challenge(session, user, district_id)
    if ch is None:
        raise ValueError("No active quest in this district")
    if ch.quest_id is None:
        raise ValueError(t(user.language, "quest.mercenary.not_quest"))
    if ch.mercenary_avatar is not None:
        raise ValueError(t(user.language, "quest.mercenary.already"))
    if user.coins < MERCENARY_HIRE_COST:
        raise ValueError(
            t(
                user.language,
                "quest.mercenary.funds",
                price=MERCENARY_HIRE_COST,
                coins=user.coins,
            )
        )

    user.coins -= MERCENARY_HIRE_COST
    ch.mercenary_avatar = avatar
    await session.flush()
