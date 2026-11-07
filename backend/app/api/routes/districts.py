"""RPG districts & quests endpoints.

Mounted under `/api/districts` (see `app/api/__init__.py`). All endpoints are
behind `CurrentUser`. The heavy lifting lives in `services.districts`; the route
is a thin serialization + ValueError→400 adapter (mirrors boss / challenges).

Quest challenges never touch the ordinary-challenge surface — that isolation is
enforced in the service / challenges layer, not here.
"""
import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, CurrentUser
from app.schemas.districts import (
    AcceptQuestResponse,
    DistrictListResponse,
    DistrictResponse,
    HireMercenaryRequest,
    InvitePartnerRequest,
)
from app.services import districts as districts_service
from app.services.districts import QuestInvitePush
from app.services.notifications import (
    send_quest_invite_accepted_push,
    send_quest_invite_declined_push,
    send_quest_invite_received_push,
)

logger = logging.getLogger(__name__)

# The City is a public feature — every authenticated user may reach these endpoints.
router = APIRouter()


def _bad_request(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


async def _fire_invite_push(push: QuestInvitePush | None) -> None:
    """Best-effort post-commit Telegram push for a co-op invite event.

    The in-app bell row was already written in the committed transaction; a push
    failure here must never surface to the caller. Content is sent in the
    recipient's language (push.lang): RU recipients get the *_ru names.
    """
    if push is None or push.telegram_id is None:
        return
    is_ru = (push.lang or "en").startswith("ru")
    quest_title = push.quest_title_ru if is_ru else push.quest_title
    district_name = push.district_name_ru if is_ru else push.district_name
    try:
        if push.kind == "received":
            await send_quest_invite_received_push(
                telegram_id=push.telegram_id,
                from_user_name=push.actor_name,
                quest_title=quest_title,
                district_name=district_name,
                quest_challenge_id=push.quest_challenge_id,
                lang=push.lang,
            )
        elif push.kind == "accepted":
            await send_quest_invite_accepted_push(
                telegram_id=push.telegram_id,
                partner_name=push.actor_name,
                quest_title=quest_title,
                quest_challenge_id=push.quest_challenge_id,
                lang=push.lang,
            )
        elif push.kind == "declined":
            await send_quest_invite_declined_push(
                telegram_id=push.telegram_id,
                partner_name=push.actor_name,
                quest_title=quest_title,
                quest_challenge_id=push.quest_challenge_id,
                lang=push.lang,
            )
    except Exception:
        logger.exception("Failed to push quest-invite %s notification", push.kind)


@router.get(
    "",
    response_model=DistrictListResponse,
    summary="List districts + per-player state",
    description=(
        "All districts with this player's live status "
        "(locked / available / active / completed), boss info, and a short "
        "active-quest summary. Computed on the fly, never persisted."
    ),
    tags=["districts"],
)
async def list_districts(user: CurrentUser, session: AsyncSessionDep):
    states = await districts_service.compute_state(session, user)
    await session.commit()
    return DistrictListResponse(
        districts=[DistrictResponse.model_validate(d) for d in states]
    )


@router.get(
    "/{district_id}",
    response_model=DistrictResponse,
    summary="District detail",
    description=(
        "One district: full bilingual content (quest, dialogue, reward) plus "
        "live quest progress (full_days and per-exercise accumulated/target) "
        "when the player has an active quest here."
    ),
    tags=["districts"],
)
async def get_district(
    district_id: str, user: CurrentUser, session: AsyncSessionDep
):
    try:
        detail = await districts_service.get_detail(session, user, district_id)
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)
    await session.commit()
    return DistrictResponse.model_validate(detail)


@router.post(
    "/{district_id}/accept",
    response_model=AcceptQuestResponse,
    summary="Accept a quest",
    description=(
        "Materialize the district's quest into a Challenge (quest_id set) and "
        "join the player as the solo participant. 400 if the district is locked, "
        "already completed, or the player already has an active quest."
    ),
    tags=["districts"],
)
async def accept_quest(
    district_id: str, user: CurrentUser, session: AsyncSessionDep
):
    try:
        challenge = await districts_service.accept_quest(session, user, district_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)
    return AcceptQuestResponse(
        challenge_id=challenge.id,
        quest_id=challenge.quest_id,
        status=challenge.status,
        start_date=challenge.start_date.isoformat(),
        end_date=challenge.end_date.isoformat(),
    )


@router.post(
    "/{district_id}/abandon",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Abandon the active quest",
    description=(
        "Abandon the player's active quest in this district. Solo instances are "
        "deleted; co-op keeps surviving partners. Mercenary coins are not "
        "refunded. 400 if there is no active quest here."
    ),
    tags=["districts"],
)
async def abandon_quest(
    district_id: str, user: CurrentUser, session: AsyncSessionDep
):
    try:
        await districts_service.abandon_quest(session, user, district_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)


@router.post(
    "/{district_id}/invite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invite a co-op partner",
    description=(
        "Invite an accepted friend to the player's active quest (co-op). Inserts "
        "a pending participant row. 400 on a non-friend, self-invite, a full "
        "party, or no active quest."
    ),
    tags=["districts"],
)
async def invite_partner(
    district_id: str,
    body: InvitePartnerRequest,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    try:
        push = await districts_service.invite_partner(
            session, user, district_id, body.user_id
        )
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)
    await _fire_invite_push(push)


@router.post(
    "/{district_id}/accept-invite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Accept a co-op invite",
    description=(
        "The invited friend accepts a pending co-op invite (pending→accepted) "
        "and the shared window is rewritten to start tomorrow. 400 if there is "
        "no pending invite, it expired, or the friend already has an active quest."
    ),
    tags=["districts"],
)
async def accept_invite(
    district_id: str, user: CurrentUser, session: AsyncSessionDep
):
    try:
        push = await districts_service.accept_invite(session, user, district_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)
    await _fire_invite_push(push)


@router.post(
    "/{district_id}/decline-invite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Decline a co-op invite",
    description=(
        "The invited friend declines a pending co-op invite. The instance stays "
        "a solo quest for the inviter. 400 if there is no pending invite."
    ),
    tags=["districts"],
)
async def decline_invite(
    district_id: str, user: CurrentUser, session: AsyncSessionDep
):
    try:
        push = await districts_service.decline_invite(session, user, district_id)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)
    await _fire_invite_push(push)


@router.post(
    "/{district_id}/hire-mercenary",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hire a cosmetic mercenary",
    description=(
        "Hire a cosmetic companion for the active quest, paid in coins. "
        "Render-only — no reward, never gates completion. 400 on insufficient "
        "funds, an already-hired mercenary, or no active quest."
    ),
    tags=["districts"],
)
async def hire_mercenary(
    district_id: str,
    body: HireMercenaryRequest,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    try:
        await districts_service.hire_mercenary(
            session, user, district_id, body.avatar
        )
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise _bad_request(e)
