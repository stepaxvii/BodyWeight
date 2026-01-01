import logging
from fastapi import APIRouter, Query
from sqlalchemy import select, func, update

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import Notification
from app.schemas import NotificationResponse, UnreadCountResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Количество непрочитанных уведомлений",
    description="Возвращает количество непрочитанных уведомлений для текущего пользователя.",
    tags=["Notifications"]
)
async def get_unread_count(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    result = await session.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == user.id)
        .where(Notification.is_read == False)
    )
    count = result.scalar() or 0
    logger.debug(f"Unread count for user {user.id}: {count}")
    return UnreadCountResponse(count=count)


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="Получить уведомления",
    description="Возвращает список уведомлений пользователя, отсортированных по дате создания (новые первыми).",
    tags=["Notifications"]
)
async def get_notifications(
    user: CurrentUser,
    session: AsyncSessionDep,
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество уведомлений"),
):
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    notifications = result.scalars().all()
    logger.debug(f"Get notifications for user {user.id}: found {len(notifications)}")
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.post("/mark-read")
async def mark_all_read(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    """Mark all notifications as read."""
    await session.execute(
        update(Notification)
        .where(Notification.user_id == user.id)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    await session.commit()
    return {"status": "ok"}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    """Mark specific notification as read."""
    await session.execute(
        update(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == user.id)
        .values(is_read=True)
    )
    await session.commit()
    return {"status": "ok"}
