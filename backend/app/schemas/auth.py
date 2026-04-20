"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr

from .users import UserResponse


class AuthRequest(BaseModel):
    """Telegram initData for authentication."""
    init_data: str


class AuthResponse(BaseModel):
    """Authentication response with user data."""
    user: UserResponse
    is_new: bool


class WebAuthResponse(BaseModel):
    """Web authentication response with JWT token."""
    user: UserResponse
    token: str
    is_new: bool = False


class WebRegisterRequest(BaseModel):
    """Web registration request."""
    email: EmailStr
    password: str
    username: str | None = None
    first_name: str | None = None


class WebLoginRequest(BaseModel):
    """Web login request. Login can be email or telegram username."""
    login: str
    password: str


class SetPasswordRequest(BaseModel):
    """Set password for TMA user to enable web login."""
    email: EmailStr
    password: str


class LinkTelegramRequest(BaseModel):
    """Request to link a Telegram account to a web account."""
    telegram_id: int


class ConfirmLinkResponse(BaseModel):
    """Response after link confirmation."""
    success: bool
    message: str
