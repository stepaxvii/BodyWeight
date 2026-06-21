"""Shop and purchase models."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user import User


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    price_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, default=1)
    sprite_url: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    purchases: Mapped[list["UserPurchase"]] = relationship(back_populates="shop_item")


class UserPurchase(Base):
    __tablename__ = "user_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    shop_item_id: Mapped[int] = mapped_column(ForeignKey("shop_items.id"))
    purchased_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="purchases")
    shop_item: Mapped["ShopItem"] = relationship(back_populates="purchases")

    __table_args__ = (UniqueConstraint("user_id", "shop_item_id", name="uq_user_purchase"),)


class UserAvatarPurchase(Base):
    __tablename__ = "user_avatar_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    avatar_id: Mapped[str] = mapped_column(String(50), nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "avatar_id", name="uq_user_avatar_purchase"),)
