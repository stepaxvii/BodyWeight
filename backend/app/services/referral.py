"""
Referral program service.

A user shares the bot invite link (t.me/<bot>?start=addfriend_<id>); when the
invitee completes their FIRST workout the inviter is rewarded with coins —
at most REFERRAL_REWARDS_CAP rewarded invites per inviter. The single source
of truth for the reward constants lives here (mirrored on the friends screen).
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.notifications import (
    save_notification,
    send_referral_reward_push,
    dispatch_in_background,
)

logger = logging.getLogger(__name__)

# Tunables
REFERRAL_REWARD_COINS = 50
REFERRAL_REWARDS_CAP = 5


async def grant_referral_reward_on_first_workout(
    session: AsyncSession,
    user: User,
    bot_push: bool = True,
) -> bool:
    """
    Reward the inviter of `user` after the invitee's first completed workout.

    Credits REFERRAL_REWARD_COINS to the inviter and bumps their
    referral_rewards_count, unless the inviter already hit REFERRAL_REWARDS_CAP.
    Creates an in-app notification for the inviter and (best-effort, off the
    request path) a Telegram push. Returns True if a reward was granted.

    The caller decides that this IS the first completed workout — this function
    only checks the referral linkage and the cap.
    """
    if user.invited_by_user_id is None:
        return False

    inviter = await session.get(User, user.invited_by_user_id)
    if not inviter:
        return False

    if inviter.referral_rewards_count >= REFERRAL_REWARDS_CAP:
        logger.info(
            "Referral reward skipped: inviter %s is at the cap (%s)",
            inviter.id,
            REFERRAL_REWARDS_CAP,
        )
        return False

    inviter.coins += REFERRAL_REWARD_COINS
    inviter.referral_rewards_count += 1

    invitee_name = user.username or user.first_name or "Пользователь"

    await save_notification(
        session=session,
        user_id=inviter.id,
        notification_type="referral_reward",
        title="Награда за приглашение!",
        message=(
            f"Твой друг {invitee_name} провёл первую тренировку! "
            f"+{REFERRAL_REWARD_COINS} монет"
        ),
        related_user_id=user.id,
    )

    if bot_push and inviter.telegram_id and inviter.notifications_enabled:
        text = (
            f"🤝 <b>Награда за приглашение!</b>\n\n"
            f"Твой друг <b>{invitee_name}</b> провёл первую тренировку.\n"
            f"Тебе начислено <b>+{REFERRAL_REWARD_COINS}</b> монет "
            f"({inviter.referral_rewards_count}/{REFERRAL_REWARDS_CAP} наград)."
        )
        dispatch_in_background(
            send_referral_reward_push(inviter.telegram_id, text)
        )

    logger.info(
        "Referral reward granted: inviter %s got +%s coins for invitee %s (%s/%s)",
        inviter.id,
        REFERRAL_REWARD_COINS,
        user.id,
        inviter.referral_rewards_count,
        REFERRAL_REWARDS_CAP,
    )
    return True
