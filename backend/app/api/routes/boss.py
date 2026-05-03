"""Monthly boss raid endpoints."""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import MonthlyBoss, BossContribution, User
from app.schemas import (
    BossResponse,
    BossLeaderboardEntry,
    BossLeaderboardResponse,
    BossMyContributionResponse,
    BossClaimResponse,
    BossHistoryEntry,
    BossHistoryResponse,
)
from app.services.boss import (
    get_or_create_current_boss,
    finalize_due_bosses,
    claim_reward,
    get_user_rank,
)


router = APIRouter()


REWARD_CLAIM_TTL_DAYS = 7


@router.get(
    "/current",
    response_model=BossResponse,
    summary="Текущий босс месяца",
    description="Возвращает активного босса для текущего месяца. Создаёт нового, если ещё не существует.",
    tags=["Boss"],
)
async def get_current_boss(user: CurrentUser, session: AsyncSessionDep):
    # Lazy finalize anything overdue (e.g. server slept past month-end)
    await finalize_due_bosses(session)
    boss = await get_or_create_current_boss(session)
    await session.commit()
    return BossResponse.model_validate(boss)


@router.get(
    "/leaderboard",
    response_model=BossLeaderboardResponse,
    summary="Лидерборд по урону по боссу",
    description="Топ-10 контрибьюторов по урону для текущего босса.",
    tags=["Boss"],
)
async def get_boss_leaderboard(user: CurrentUser, session: AsyncSessionDep):
    boss = await get_or_create_current_boss(session)

    result = await session.execute(
        select(BossContribution, User)
        .join(User, BossContribution.user_id == User.id)
        .where(BossContribution.boss_id == boss.id)
        .order_by(BossContribution.total_damage.desc())
        .limit(10)
    )
    entries: list[BossLeaderboardEntry] = []
    for rank, (contrib, leader) in enumerate(result.all(), start=1):
        entries.append(
            BossLeaderboardEntry(
                rank=rank,
                user_id=leader.id,
                username=leader.username,
                first_name=leader.first_name,
                avatar_id=leader.avatar_id,
                total_damage=contrib.total_damage,
                attacks_count=contrib.attacks_count,
            )
        )

    await session.commit()
    return BossLeaderboardResponse(boss_id=boss.id, entries=entries)


@router.get(
    "/me",
    response_model=BossMyContributionResponse,
    summary="Мой вклад по текущему боссу",
    description="Возвращает урон, ранг и доступную награду для текущего пользователя.",
    tags=["Boss"],
)
async def get_my_contribution(user: CurrentUser, session: AsyncSessionDep):
    boss = await get_or_create_current_boss(session)

    contrib_result = await session.execute(
        select(BossContribution).where(
            BossContribution.boss_id == boss.id,
            BossContribution.user_id == user.id,
        )
    )
    contrib = contrib_result.scalar_one_or_none()

    if contrib is None:
        await session.commit()
        return BossMyContributionResponse(
            boss_id=boss.id,
            rank=None,
            total_damage=0,
            attacks_count=0,
            last_attack_at=None,
            reward_tier=None,
            reward_coins=0,
            is_top10=False,
            reward_claimable=False,
            reward_claimed_at=None,
        )

    rank, _ = await get_user_rank(session, boss.id, user.id)

    is_claimable = (
        boss.finalized_at is not None
        and contrib.reward_claimed_at is None
        and contrib.reward_coins > 0
        and datetime.utcnow()
        <= boss.finalized_at + timedelta(days=REWARD_CLAIM_TTL_DAYS)
    )

    await session.commit()
    return BossMyContributionResponse(
        boss_id=boss.id,
        rank=rank,
        total_damage=contrib.total_damage,
        attacks_count=contrib.attacks_count,
        last_attack_at=contrib.last_attack_at,
        reward_tier=contrib.reward_tier,
        reward_coins=contrib.reward_coins,
        is_top10=contrib.is_top10,
        reward_claimable=is_claimable,
        reward_claimed_at=contrib.reward_claimed_at,
    )


@router.post(
    "/{boss_id}/claim",
    response_model=BossClaimResponse,
    summary="Забрать награду за босса",
    description="Зачисляет монеты на счёт пользователя за участие. Доступно 7 дней после финализации.",
    tags=["Boss"],
)
async def claim_boss_reward(
    boss_id: int,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    try:
        coins = await claim_reward(session, user, boss_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return BossClaimResponse(coins_awarded=coins)


@router.get(
    "/history",
    response_model=BossHistoryResponse,
    summary="История боссов",
    description="Список прошедших боссов и личный результат игрока по каждому. Возвращает до 12 последних.",
    tags=["Boss"],
)
async def get_boss_history(user: CurrentUser, session: AsyncSessionDep):
    # Pull most recent 12 bosses (newest first)
    bosses_result = await session.execute(
        select(MonthlyBoss).order_by(MonthlyBoss.start_date.desc()).limit(12)
    )
    bosses = list(bosses_result.scalars().all())
    if not bosses:
        await session.commit()
        return BossHistoryResponse(bosses=[])

    # Pull all my contributions for those bosses in one query
    boss_ids = [b.id for b in bosses]
    contrib_result = await session.execute(
        select(BossContribution).where(
            BossContribution.boss_id.in_(boss_ids),
            BossContribution.user_id == user.id,
        )
    )
    contribs_by_boss = {c.boss_id: c for c in contrib_result.scalars().all()}

    entries: list[BossHistoryEntry] = []
    for boss in bosses:
        contrib = contribs_by_boss.get(boss.id)
        rank = None
        if contrib and contrib.total_damage > 0:
            rank, _ = await get_user_rank(session, boss.id, user.id)
        entries.append(
            BossHistoryEntry(
                id=boss.id,
                name_ru=boss.name_ru,
                image_emoji=boss.image_emoji,
                image_url=boss.image_url,
                theme=boss.theme,
                start_date=boss.start_date,
                end_date=boss.end_date,
                status=boss.status,
                my_total_damage=contrib.total_damage if contrib else 0,
                my_rank=rank,
                my_reward_coins=contrib.reward_coins if contrib else 0,
                my_reward_claimed=(
                    contrib is not None and contrib.reward_claimed_at is not None
                ),
            )
        )

    await session.commit()
    return BossHistoryResponse(bosses=entries)
