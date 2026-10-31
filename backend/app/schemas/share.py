"""Workout share card Pydantic schemas."""

from pydantic import BaseModel


class ShareWorkoutResponse(BaseModel):
    """Response for POST /share/workout/{session_id}.

    ``prepared_message_id`` is None when the Telegram prepare call failed or
    the user has no telegram_id — the frontend then falls back to a
    t.me/share/url link share.
    """
    card_url: str
    story_url: str
    prepared_message_id: str | None = None
    invite_link: str
    share_text: str
