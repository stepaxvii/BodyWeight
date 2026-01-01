"""Common schemas used across the API."""

from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool
