"""
Notification management routes.

Provides endpoint for triggering notification checks (for cron/scheduler).
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from app.api.deps import AsyncSessionDep
from app.config import settings
from app.services.scheduler import run_notification_checks

router = APIRouter()


class NotificationCheckResponse(BaseModel):
    daily_reminders: int
    inactivity_reminders: int


@router.post("/check", response_model=NotificationCheckResponse)
async def trigger_notification_check(
    session: AsyncSessionDep,
    x_cron_secret: str = Header(None, alias="X-Cron-Secret"),
):
    """
    Trigger notification check.

    This endpoint should be called every minute by a cron job or scheduler.
    Requires X-Cron-Secret header matching SECRET_KEY for security.
    """
    # Verify secret to prevent unauthorized access
    if x_cron_secret != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    results = await run_notification_checks(session)

    return NotificationCheckResponse(**results)
