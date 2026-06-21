"""Per-user daily activity norm, versioned by effective date.

The norm is the target XP per day used to colour the activity calendar.
``users.daily_activity_norm`` holds the *current* value (cheap reads, flows
through ``UserResponse``); this table records the full history so each calendar
day can be coloured against the norm that was in force on that date.
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


class UserActivityNorm(Base):
    __tablename__ = "user_activity_norms"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Target XP per day, in force from ``effective_from`` until the next row.
    norm: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "effective_from", name="uq_activity_norm_user_date"),
    )

    user: Mapped["User"] = relationship(back_populates="activity_norms")
