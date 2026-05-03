"""User-created challenges endpoints."""
from datetime import datetime, timedelta, date
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import (
    Challenge,
    ChallengeExercise,
    ChallengeParticipant,
    ChallengeProgress,
    Exercise,
    User,
)
from app.schemas import (
    ChallengeCreate,
    ChallengeExerciseResponse,
    ChallengeListItem,
    ChallengeParticipantInfo,
    ChallengeDayProgress,
    ChallengeDetailsResponse,
    ChallengeMyCalendarResponse,
    ChallengeClaimResponse,
)
from app.services.challenges import (
    CreateChallengeInput,
    ChallengeExerciseInput,
    create_challenge,
    join_challenge,
    update_challenge_status,
    update_all_statuses,
    finalize_due_challenges,
    finalize_challenge,
    claim_reward,
    REWARD_CLAIM_TTL_DAYS,
)


router = APIRouter()


def _user_display_name(u: User | None) -> str | None:
    if u is None:
        return None
    return u.username or u.first_name or None


async def _calc_running_completion(
    session: AsyncSessionDep,
    challenge: Challenge,
    user_id: int,
) -> tuple[int, int]:
    """
    Returns (completion_percent, completed_days) computed from progress rows.
    Used while challenge is still running (before finalization).
    A day fully complete = ALL exercises completed for that day.
    """
    duration = (challenge.end_date - challenge.start_date).days + 1
    if duration <= 0:
        return 0, 0

    n_ex_result = await session.execute(
        select(func.count(ChallengeExercise.id)).where(
            ChallengeExercise.challenge_id == challenge.id
        )
    )
    n_ex = n_ex_result.scalar() or 0
    if n_ex == 0:
        return 0, 0

    rows = await session.execute(
        select(ChallengeProgress.progress_date)
        .where(ChallengeProgress.challenge_id == challenge.id)
        .where(ChallengeProgress.user_id == user_id)
        .where(ChallengeProgress.completed.is_(True))
    )
    counts: dict = {}
    for (d,) in rows.all():
        counts[d] = counts.get(d, 0) + 1
    full_days = sum(1 for v in counts.values() if v >= n_ex)
    pct = min(100, int(round(100 * full_days / duration)))
    return pct, full_days


# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ChallengeDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать челлендж",
    tags=["Challenges"],
)
async def create_challenge_route(
    body: ChallengeCreate,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    try:
        challenge = await create_challenge(
            session,
            user,
            CreateChallengeInput(
                title=body.title,
                description=body.description,
                start_date=body.start_date,
                end_date=body.end_date,
                exercises=[
                    ChallengeExerciseInput(
                        exercise_slug=e.exercise_slug,
                        daily_target=e.daily_target,
                    )
                    for e in body.exercises
                ],
            ),
        )
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return await _build_details_response(session, user, challenge.id)


@router.get(
    "",
    response_model=list[ChallengeListItem],
    summary="Каталог челленджей",
    tags=["Challenges"],
)
async def list_challenges_route(
    user: CurrentUser,
    session: AsyncSessionDep,
    status_filter: str | None = Query(None, alias="status"),
    mine: bool = False,
):
    # Refresh statuses lazily so newly-active/finished challenges show right state
    await update_all_statuses(session)
    await finalize_due_challenges(session)

    query = select(Challenge).order_by(Challenge.start_date.desc())

    if status_filter in ("upcoming", "active", "finished"):
        query = query.where(Challenge.status == status_filter)

    if mine:
        query = query.join(
            ChallengeParticipant,
            ChallengeParticipant.challenge_id == Challenge.id,
        ).where(ChallengeParticipant.user_id == user.id)

    challenges = list((await session.execute(query)).scalars().unique())

    if not challenges:
        await session.commit()
        return []

    ids = [c.id for c in challenges]

    # Aggregate counts
    parts_q = await session.execute(
        select(ChallengeParticipant.challenge_id, func.count(ChallengeParticipant.id))
        .where(ChallengeParticipant.challenge_id.in_(ids))
        .group_by(ChallengeParticipant.challenge_id)
    )
    parts_count = {cid: cnt for cid, cnt in parts_q.all()}

    ex_q = await session.execute(
        select(ChallengeExercise.challenge_id, func.count(ChallengeExercise.id))
        .where(ChallengeExercise.challenge_id.in_(ids))
        .group_by(ChallengeExercise.challenge_id)
    )
    ex_count = {cid: cnt for cid, cnt in ex_q.all()}

    # My memberships
    me_q = await session.execute(
        select(ChallengeParticipant.challenge_id)
        .where(ChallengeParticipant.user_id == user.id)
        .where(ChallengeParticipant.challenge_id.in_(ids))
    )
    my_ids = {r[0] for r in me_q.all()}

    # Creator names
    creator_ids = [c.creator_user_id for c in challenges if c.creator_user_id is not None]
    creator_map: dict[int, User] = {}
    if creator_ids:
        cr_q = await session.execute(select(User).where(User.id.in_(creator_ids)))
        for u in cr_q.scalars().all():
            creator_map[u.id] = u

    items = [
        ChallengeListItem(
            id=c.id,
            title=c.title,
            creator_user_id=c.creator_user_id,
            creator_name=_user_display_name(creator_map.get(c.creator_user_id)) if c.creator_user_id else None,
            start_date=c.start_date,
            end_date=c.end_date,
            status=c.status,
            participants_count=parts_count.get(c.id, 0),
            exercises_count=ex_count.get(c.id, 0),
            is_member=c.id in my_ids,
        )
        for c in challenges
    ]
    await session.commit()
    return items


@router.get(
    "/{challenge_id}",
    response_model=ChallengeDetailsResponse,
    summary="Детали челленджа",
    tags=["Challenges"],
)
async def get_challenge_route(
    challenge_id: int,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    return await _build_details_response(session, user, challenge_id)


@router.post(
    "/{challenge_id}/join",
    response_model=ChallengeDetailsResponse,
    summary="Присоединиться к челленджу",
    tags=["Challenges"],
)
async def join_challenge_route(
    challenge_id: int,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    try:
        await join_challenge(session, user, challenge_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return await _build_details_response(session, user, challenge_id)


@router.get(
    "/{challenge_id}/calendar",
    response_model=ChallengeMyCalendarResponse,
    summary="Календарь прогресса игрока в челлендже",
    tags=["Challenges"],
)
async def get_calendar_route(
    challenge_id: int,
    user: CurrentUser,
    session: AsyncSessionDep,
    user_id: int | None = Query(None),
):
    """If user_id is omitted, returns calendar for the current user."""
    target_uid = user_id or user.id
    challenge = await session.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(404, "Challenge not found")

    rows_result = await session.execute(
        select(ChallengeProgress, Exercise)
        .join(Exercise, Exercise.id == ChallengeProgress.exercise_id)
        .where(ChallengeProgress.challenge_id == challenge_id)
        .where(ChallengeProgress.user_id == target_uid)
        .order_by(ChallengeProgress.progress_date, Exercise.id)
    )

    rows = [
        ChallengeDayProgress(
            progress_date=p.progress_date,
            exercise_id=ex.id,
            exercise_slug=ex.slug,
            exercise_name_ru=ex.name_ru,
            accumulated=p.accumulated,
            target=p.target,
            completed=p.completed,
        )
        for p, ex in rows_result.all()
    ]

    await session.commit()
    return ChallengeMyCalendarResponse(challenge_id=challenge_id, rows=rows)


@router.post(
    "/{challenge_id}/claim",
    response_model=ChallengeClaimResponse,
    summary="Забрать награду за челлендж",
    tags=["Challenges"],
)
async def claim_route(
    challenge_id: int,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    try:
        coins = await claim_reward(session, user, challenge_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return ChallengeClaimResponse(coins_awarded=coins)


# ---------------------------------------------------------------------------


async def _build_details_response(
    session: AsyncSessionDep,
    user: User,
    challenge_id: int,
) -> ChallengeDetailsResponse:
    """Shared assembler for detail responses (create / get / join)."""
    challenge = await session.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(404, "Challenge not found")

    # Lazy lifecycle transitions on read
    if await update_challenge_status(session, challenge):
        await session.flush()
    if challenge.status == "finished" and challenge.finalized_at is None:
        await finalize_challenge(session, challenge)
        await session.flush()

    # Exercises
    ex_q = await session.execute(
        select(ChallengeExercise, Exercise)
        .join(Exercise, Exercise.id == ChallengeExercise.exercise_id)
        .where(ChallengeExercise.challenge_id == challenge.id)
        .order_by(ChallengeExercise.order_index)
    )
    exercises = [
        ChallengeExerciseResponse(
            exercise_id=ex.id,
            exercise_slug=ex.slug,
            exercise_name_ru=ex.name_ru,
            daily_target=ce.daily_target,
            is_timed=ce.is_timed,
            order_index=ce.order_index,
        )
        for ce, ex in ex_q.all()
    ]

    # Participants + their info
    parts_q = await session.execute(
        select(ChallengeParticipant, User)
        .join(User, User.id == ChallengeParticipant.user_id)
        .where(ChallengeParticipant.challenge_id == challenge.id)
    )
    participants_rows = list(parts_q.all())

    participants: list[ChallengeParticipantInfo] = []
    for p, u in participants_rows:
        if challenge.finalized_at is not None and p.completion_percent is not None:
            pct = p.completion_percent
            pct_running, completed_days = await _calc_running_completion(
                session, challenge, u.id
            )
            # Final % may differ slightly from running due to clamp; prefer stored.
        else:
            pct, completed_days = await _calc_running_completion(
                session, challenge, u.id
            )

        is_claimable = (
            challenge.finalized_at is not None
            and p.reward_claimed_at is None
            and p.reward_coins > 0
            and datetime.utcnow()
            <= challenge.finalized_at + timedelta(days=REWARD_CLAIM_TTL_DAYS)
        )

        participants.append(
            ChallengeParticipantInfo(
                user_id=u.id,
                username=u.username,
                first_name=u.first_name,
                avatar_id=u.avatar_id,
                completion_percent=pct,
                completed_days=completed_days,
                reward_tier=p.reward_tier,
                reward_coins=p.reward_coins,
                reward_claimable=is_claimable,
                reward_claimed_at=p.reward_claimed_at,
            )
        )

    # Sort participants: me first, then by % desc, then by joined order
    participants.sort(key=lambda x: (-int(x.user_id == user.id), -x.completion_percent))

    is_member = any(pi.user_id == user.id for pi in participants)
    can_join = (challenge.status == "upcoming") and not is_member

    creator = None
    if challenge.creator_user_id:
        creator = await session.get(User, challenge.creator_user_id)

    duration_days = (challenge.end_date - challenge.start_date).days + 1

    await session.commit()
    return ChallengeDetailsResponse(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        creator_user_id=challenge.creator_user_id,
        creator_name=_user_display_name(creator),
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        duration_days=duration_days,
        status=challenge.status,
        finalized_at=challenge.finalized_at,
        exercises=exercises,
        participants=participants,
        is_member=is_member,
        can_join=can_join,
    )
