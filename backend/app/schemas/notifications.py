"""Notification-related Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Notification response schema."""
    id: int
    notification_type: str
    title: str
    message: str
    is_read: bool
    related_user_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    """Unread notifications count response schema."""
    count: int
