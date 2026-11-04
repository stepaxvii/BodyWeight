"""Workout share card Pydantic schemas."""

from pydantic import BaseModel, Field


class ShareWorkoutRequest(BaseModel):
    """Optional body for POST /share/workout/{session_id}."""
    routine_name: str | None = Field(
        default=None, max_length=120,
        description="Название рутины для заголовка текстового отчёта",
    )


class ShareWorkoutResponse(BaseModel):
    """Response for POST /share/workout/{session_id}.

    ``prepared_message_id`` (PNG card) and ``prepared_text_message_id``
    (text report with the full exercise list) are None when the Telegram
    prepare call failed or the user has no telegram_id — the frontend then
    falls back to a t.me/share/url link share.
    """
    card_url: str
    story_url: str
    prepared_message_id: str | None = None
    prepared_text_message_id: str | None = None
    invite_link: str
    share_text: str
