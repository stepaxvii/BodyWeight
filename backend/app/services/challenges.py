"""
User-created challenge service.

Lifecycle:
- created (status=upcoming) -> joinable
- start_date reached -> status=active (no more joins)
- end_date passed -> status=finished -> finalize() awards tiers
- claim() collects coins, TTL 7 days

Progress recording (called from workout_processor):
- For each active challenge user joined, for each exercise in the challenge
  that appears in the workout, accumulate min(reps_in_workout, remaining_target).
- Reps beyond target still count toward general XP/achievements (handled
  separately in workout_processor) — challenge only credits up to target.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Iterable

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Challenge,
    ChallengeExercise,
    ChallengeParticipant,
    ChallengeProgress,
    Exercise,
    User,
)
from app.services.notifications import save_notification

logger = logging.getLogger(__name__)


# Tier thresholds by completion percentage
REWARD_TIERS = [
    # (min_percent, tier_id, coins)
    (100, "tier_perfect", 200),
    (80, "tier_high", 100),
    (50, "tier_mid", 40),
    (1, "tier_participant", 10),
]
REWARD_CLAIM_TTL_DAYS = 7

# Sanity caps for created challenges
MIN_DURATION_DAYS = 3
MAX_DURATION_DAYS = 365
MAX_TITLE_LEN = 120
MAX_EXERCISES = 5


@dataclass
class ChallengeExerciseInput:
    exercise_slug: str
    daily_target: int


@dataclass
class CreateChallengeInput:
    title: str
    description: str | None
    start_date: date
    end_date: date
    exercises: list[ChallengeExerciseInput]


# ---------------------------------------------------------------------------
# Status transitions (lazy)
# ---------------------------------------------------------------------------

async def update_challenge_status(session: AsyncSession, challenge: Challenge) -> bool:
    """Refresh challenge status based on current UTC date. Returns True if changed."""
    today = datetime.utcnow().date()
    new_status = challenge.status

    if challenge.status == "upcoming" and today >= challenge.start_date:
        new_status = "active"
    if challenge.status in ("upcoming", "active") and today > challenge.end_date:
        new_status = "finished"

    if new_status != challenge.status:
        challenge.status = new_status
        return True
    return False


async def update_all_statuses(session: AsyncSession) -> int:
    """Lazy bulk transition for cron / API calls. Returns number changed."""
    today = datetime.utcnow().date()
    result = await session.execute(
        select(Challenge).where(Challenge.status.in_(["upcoming", "active"]))
    )
    changed = 0
    for ch in result.scalars().all():
        if await update_challenge_status(session, ch):
            changed += 1
    return changed


# ---------------------------------------------------------------------------
# Creation & joining
# ---------------------------------------------------------------------------

async def create_challenge(
    session: AsyncSession,
    creator: User,
    data: CreateChallengeInput,
) -> Challenge:
    """Create a new challenge and auto-add the creator as the first participant."""
    title = (data.title or "").strip()
    if not title:
        raise ValueError("Title is required")
    if len(title) > MAX_TITLE_LEN:
        raise ValueError(f"Title too long (max {MAX_TITLE_LEN})")

    today = datetime.utcnow().date()
    if data.start_date < today:
        raise ValueError("start_date cannot be in the past")
    duration = (data.end_date - data.start_date).days + 1
    if duration < MIN_DURATION_DAYS:
        raise ValueError(f"Challenge too short (min {MIN_DURATION_DAYS} days)")
    if duration > MAX_DURATION_DAYS:
        raise ValueError(f"Challenge too long (max {MAX_DURATION_DAYS} days)")

    if not data.exercises:
        raise ValueError("Add at least one exercise")
    if len(data.exercises) > MAX_EXERCISES:
        raise ValueError(f"Too many exercises (max {MAX_EXERCISES})")

    # Resolve exercises by slug, validating uniqueness and existence
    seen_slugs: set[str] = set()
    resolved: list[tuple[Exercise, int]] = []
    for ex_in in data.exercises:
        slug = ex_in.exercise_slug
        if slug in seen_slugs:
            raise ValueError(f"Duplicate exercise: {slug}")
        seen_slugs.add(slug)
        if ex_in.daily_target <= 0:
            raise ValueError(f"daily_target for '{slug}' must be positive")

        ex_result = await session.execute(
            select(Exercise).where(Exercise.slug == slug)
        )
        exercise = ex_result.scalar_one_or_none()
        if exercise is None:
            raise ValueError(f"Unknown exercise: {slug}")
        resolved.append((exercise, ex_in.daily_target))

    challenge = Challenge(
        creator_user_id=creator.id,
        title=title,
        description=(data.description or "").strip() or None,
        start_date=data.start_date,
        end_date=data.end_date,
        status="upcoming" if data.start_date > today else "active",
    )
    session.add(challenge)
    await session.flush()

    for idx, (exercise, target) in enumerate(resolved):
        session.add(
            ChallengeExercise(
                challenge_id=challenge.id,
                exercise_id=exercise.id,
                daily_target=target,
                is_timed=bool(exercise.is_timed),
                order_index=idx,
            )
        )

    # Creator is the first participant
    session.add(
        ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=creator.id,
        )
    )

    await session.flush()
    return challenge


async def join_challenge(
    session: AsyncSession,
    user: User,
    challenge_id: int,
) -> ChallengeParticipant:
    """User joins an upcoming challenge. Cannot join after start."""
    challenge = await session.get(Challenge, challenge_id)
    if challenge is None:
        raise ValueError("Challenge not found")

    # Lazy status refresh in case start_date hit
    await update_challenge_status(session, challenge)

    if challenge.status != "upcoming":
        raise ValueError("Joining is closed; challenge already started")

    # Already a participant?
    existing = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id,
            ChallengeParticipant.user_id == user.id,
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    p = ChallengeParticipant(challenge_id=challenge_id, user_id=user.id)
    session.add(p)
    await session.flush()
    return p


# ---------------------------------------------------------------------------
# Progress recording (called from workout_processor)
# ---------------------------------------------------------------------------

async def record_progress(
    session: AsyncSession,
    user: User,
    workout_date: date,
    reps_by_slug: dict[str, int],
) -> None:
    """
    Update progress in all active challenges this user participates in.

    `reps_by_slug` maps exercise slug -> total reps performed in this workout.
    For timed exercises, pass total seconds (semantics: target == seconds).

    Caps each contribution at remaining target (excess does not count).
    """
    if not reps_by_slug:
        return

    # Find active challenges where the user is a participant AND that contain
    # at least one of the workout's exercises.
    result = await session.execute(
        select(Challenge, ChallengeExercise, Exercise)
        .join(ChallengeParticipant, ChallengeParticipant.challenge_id == Challenge.id)
        .join(ChallengeExercise, ChallengeExercise.challenge_id == Challenge.id)
        .join(Exercise, Exercise.id == ChallengeExercise.exercise_id)
        .where(ChallengeParticipant.user_id == user.id)
        .where(Challenge.status == "active")
        .where(Challenge.start_date <= workout_date)
        .where(Challenge.end_date >= workout_date)
        .where(Exercise.slug.in_(list(reps_by_slug.keys())))
    )
    rows = result.all()

    for challenge, ch_ex, exercise in rows:
        reps = reps_by_slug.get(exercise.slug, 0)
        if reps <= 0:
            continue

        # Find or create progress row for (challenge, user, exercise, date)
        prog_result = await session.execute(
            select(ChallengeProgress).where(
                ChallengeProgress.challenge_id == challenge.id,
                ChallengeProgress.user_id == user.id,
                ChallengeProgress.exercise_id == exercise.id,
                ChallengeProgress.progress_date == workout_date,
            )
        )
        prog = prog_result.scalar_one_or_none()
        if prog is None:
            prog = ChallengeProgress(
                challenge_id=challenge.id,
                user_id=user.id,
                exercise_id=exercise.id,
                progress_date=workout_date,
                accumulated=0,
                target=ch_ex.daily_target,
                completed=False,
            )
            session.add(prog)

        if prog.completed:
            continue  # already capped

        remaining = max(0, prog.target - prog.accumulated)
        to_add = min(reps, remaining)
        if to_add <= 0:
            continue

        prog.accumulated += to_add
        if prog.accumulated >= prog.target:
            prog.completed = True


# ---------------------------------------------------------------------------
# Finalization & rewards
# ---------------------------------------------------------------------------

async def _participant_completion_percent(
    session: AsyncSession,
    challenge: Challenge,
    user_id: int,
) -> int:
    """
    Compute % of completed days for a participant.
    A day is completed only if ALL exercises hit target that day (AND).

    Days = (end_date - start_date + 1).
    """
    duration = (challenge.end_date - challenge.start_date).days + 1
    if duration <= 0:
        return 0

    # Count exercises in this challenge
    ex_result = await session.execute(
        select(func.count(ChallengeExercise.id)).where(
            ChallengeExercise.challenge_id == challenge.id
        )
    )
    n_exercises = ex_result.scalar() or 0
    if n_exercises == 0:
        return 0

    # Count progress rows that are completed for this user grouped by date.
    # A day fully complete = exactly n_exercises completed rows for that date.
    rows = await session.execute(
        select(ChallengeProgress.progress_date)
        .where(ChallengeProgress.challenge_id == challenge.id)
        .where(ChallengeProgress.user_id == user_id)
        .where(ChallengeProgress.completed.is_(True))
    )
    counts: dict[date, int] = {}
    for (d,) in rows.all():
        counts[d] = counts.get(d, 0) + 1

    full_days = sum(1 for v in counts.values() if v >= n_exercises)
    return min(100, int(round(100 * full_days / duration)))


async def finalize_challenge(session: AsyncSession, challenge: Challenge) -> None:
    """
    Resolve all participants' rewards based on completion %. Idempotent.
    """
    if challenge.finalized_at is not None:
        return

    # Make sure we're in finished state
    today = datetime.utcnow().date()
    if today <= challenge.end_date:
        return  # not yet
    challenge.status = "finished"

    # Pull all participants
    result = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge.id
        )
    )
    participants = list(result.scalars().all())

    for p in participants:
        pct = await _participant_completion_percent(session, challenge, p.user_id)
        p.completion_percent = pct
        tier_id, coins = _resolve_tier(pct)
        p.reward_tier = tier_id
        p.reward_coins = coins

    challenge.finalized_at = datetime.utcnow()

    # Notify everyone who joined
    for p in participants:
        await save_notification(
            session=session,
            user_id=p.user_id,
            notification_type="challenge_finished",
            title="Челлендж завершён",
            message=f"«{challenge.title}»: ты выполнил {p.completion_percent}%. Забери награду!",
        )


def _resolve_tier(pct: int) -> tuple[str | None, int]:
    for min_pct, tier_id, coins in REWARD_TIERS:
        if pct >= min_pct:
            return tier_id, coins
    return None, 0


async def finalize_due_challenges(session: AsyncSession) -> int:
    today = datetime.utcnow().date()
    result = await session.execute(
        select(Challenge)
        .where(Challenge.finalized_at.is_(None))
        .where(Challenge.end_date < today)
    )
    bosses = list(result.scalars().all())
    for ch in bosses:
        await finalize_challenge(session, ch)
    return len(bosses)


async def claim_reward(
    session: AsyncSession,
    user: User,
    challenge_id: int,
) -> int:
    """Claim coins for a finalized challenge. Returns coins awarded."""
    result = await session.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id,
            ChallengeParticipant.user_id == user.id,
        )
    )
    p = result.scalar_one_or_none()
    if p is None:
        raise ValueError("Not a participant")
    if p.reward_claimed_at is not None:
        raise ValueError("Reward already claimed")

    challenge = await session.get(Challenge, challenge_id)
    if challenge is None or challenge.finalized_at is None:
        raise ValueError("Challenge not finalized yet")

    if datetime.utcnow() > challenge.finalized_at + timedelta(days=REWARD_CLAIM_TTL_DAYS):
        raise ValueError("Reward window expired")

    if p.reward_coins > 0:
        user.coins += p.reward_coins
    p.reward_claimed_at = datetime.utcnow()

    return p.reward_coins
