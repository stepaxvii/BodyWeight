"""Friend-related Pydantic schemas."""

from pydantic import BaseModel


class FriendResponse(BaseModel):
    """Friend response schema."""
    id: int
    user_id: int
    username: str | None
    first_name: str | None
    avatar_id: str
    level: int
    total_xp: int
    current_streak: int
    status: str

    class Config:
        from_attributes = True


class AddFriendRequest(BaseModel):
    """Request schema for adding a friend."""
    user_id: int | None = None
    username: str | None = None
