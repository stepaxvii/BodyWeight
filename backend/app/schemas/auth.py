"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel

from .users import UserResponse


class AuthRequest(BaseModel):
    """Telegram initData for authentication."""
    init_data: str


class AuthResponse(BaseModel):
    """Authentication response with user data."""
    user: UserResponse
    is_new: bool
