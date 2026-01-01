"""Shop-related Pydantic schemas."""

from pydantic import BaseModel


class ShopItemResponse(BaseModel):
    """Shop item response schema."""
    id: int
    slug: str
    name: str
    name_ru: str
    item_type: str
    price_coins: int
    required_level: int
    sprite_url: str | None
    owned: bool = False
    equipped: bool = False

    class Config:
        from_attributes = True


class InventoryItemResponse(BaseModel):
    """Inventory item response schema."""
    id: int
    shop_item: ShopItemResponse
    is_equipped: bool
    purchased_at: str

    class Config:
        from_attributes = True
