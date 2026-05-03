"""Monthly boss raid models."""
from datetime import datetime, date
from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user import User


class MonthlyBoss(Base):
    __tablename__ = "monthly_bosses"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)
    image_emoji: Mapped[str] = mapped_column(String(16), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    theme: Mapped[str] = mapped_column(String(30), nullable=False)
    legend_ru: Mapped[str] = mapped_column(Text, nullable=False)

    max_hp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_hp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # UTC start/end of month
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # 'active' | 'defeated' | 'expired'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    defeated_at: Mapped[datetime | None] = mapped_column(DateTime)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    contributions: Mapped[list["BossContribution"]] = relationship(
        back_populates="boss", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("start_date", name="uq_monthly_boss_start"),
    )


class BossContribution(Base):
    __tablename__ = "boss_contributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    boss_id: Mapped[int] = mapped_column(ForeignKey("monthly_bosses.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    total_damage: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    attacks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attack_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Reward tier resolved at finalization; null until boss closes.
    # 'tier1' (5c) | 'tier2' (15c) | 'tier3' (50c) | 'tier4' (150c)
    reward_tier: Mapped[str | None] = mapped_column(String(20))
    reward_coins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_top10: Mapped[bool] = mapped_column(default=False)
    reward_claimed_at: Mapped[datetime | None] = mapped_column(DateTime)

    boss: Mapped["MonthlyBoss"] = relationship(back_populates="contributions")
    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("boss_id", "user_id", name="uq_boss_user"),
        Index("idx_boss_user", "boss_id", "user_id"),
        Index("idx_boss_damage", "boss_id", "total_damage"),
    )
