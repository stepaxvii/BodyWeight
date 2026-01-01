from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import ShopItem, UserPurchase
from app.schemas import ShopItemResponse, InventoryItemResponse

router = APIRouter()


@router.get("", response_model=list[ShopItemResponse])
async def get_shop_items(
    session: AsyncSessionDep,
    user: CurrentUser,
    item_type: str | None = None,
):
    """Get all shop items."""
    query = select(ShopItem).where(ShopItem.is_active == True)

    if item_type:
        query = query.where(ShopItem.item_type == item_type)

    query = query.order_by(ShopItem.required_level, ShopItem.price_coins)

    result = await session.execute(query)
    items = result.scalars().all()

    # Get user's purchases
    purchases_result = await session.execute(
        select(UserPurchase)
        .where(UserPurchase.user_id == user.id)
    )
    purchases = {p.shop_item_id: p for p in purchases_result.scalars().all()}

    return [
        ShopItemResponse(
            id=item.id,
            slug=item.slug,
            name=item.name,
            name_ru=item.name_ru,
            item_type=item.item_type,
            price_coins=item.price_coins,
            required_level=item.required_level,
            sprite_url=item.sprite_url,
            owned=item.id in purchases,
            equipped=purchases[item.id].is_equipped if item.id in purchases else False,
        )
        for item in items
    ]


@router.post("/purchase/{item_id}", response_model=ShopItemResponse)
async def purchase_item(
    item_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Purchase a shop item."""
    # Get item
    result = await session.execute(
        select(ShopItem)
        .where(ShopItem.id == item_id)
        .where(ShopItem.is_active == True)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Check if already owned
    purchase_result = await session.execute(
        select(UserPurchase)
        .where(UserPurchase.user_id == user.id)
        .where(UserPurchase.shop_item_id == item_id)
    )
    existing = purchase_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item already owned",
        )

    # Check level requirement
    if user.level < item.required_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requires level {item.required_level}",
        )

    # Check coins
    if user.coins < item.price_coins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough coins. Need {item.price_coins}, have {user.coins}",
        )

    # Purchase
    user.coins -= item.price_coins

    purchase = UserPurchase(
        user_id=user.id,
        shop_item_id=item_id,
        is_equipped=False,
    )
    session.add(purchase)
    await session.flush()

    return ShopItemResponse(
        id=item.id,
        slug=item.slug,
        name=item.name,
        name_ru=item.name_ru,
        item_type=item.item_type,
        price_coins=item.price_coins,
        required_level=item.required_level,
        sprite_url=item.sprite_url,
        owned=True,
        equipped=False,
    )


@router.get("/inventory", response_model=list[InventoryItemResponse])
async def get_inventory(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get user's purchased items."""
    result = await session.execute(
        select(UserPurchase, ShopItem)
        .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
        .where(UserPurchase.user_id == user.id)
        .order_by(UserPurchase.purchased_at.desc())
    )
    rows = result.all()

    return [
        InventoryItemResponse(
            id=purchase.id,
            shop_item=ShopItemResponse(
                id=item.id,
                slug=item.slug,
                name=item.name,
                name_ru=item.name_ru,
                item_type=item.item_type,
                price_coins=item.price_coins,
                required_level=item.required_level,
                sprite_url=item.sprite_url,
                owned=True,
                equipped=purchase.is_equipped,
            ),
            is_equipped=purchase.is_equipped,
            purchased_at=purchase.purchased_at.isoformat(),
        )
        for purchase, item in rows
    ]


@router.post("/equip/{purchase_id}", response_model=InventoryItemResponse)
async def equip_item(
    purchase_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Equip a purchased item."""
    result = await session.execute(
        select(UserPurchase, ShopItem)
        .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
        .where(UserPurchase.id == purchase_id)
        .where(UserPurchase.user_id == user.id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in inventory",
        )

    purchase, item = row

    # Unequip other items of same type
    await session.execute(
        select(UserPurchase)
        .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
        .where(UserPurchase.user_id == user.id)
        .where(ShopItem.item_type == item.item_type)
        .where(UserPurchase.is_equipped == True)
    )

    # For each equipped item of same type, unequip
    unequip_result = await session.execute(
        select(UserPurchase)
        .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
        .where(UserPurchase.user_id == user.id)
        .where(ShopItem.item_type == item.item_type)
        .where(UserPurchase.is_equipped == True)
    )
    for other_purchase in unequip_result.scalars().all():
        other_purchase.is_equipped = False

    # Equip selected item
    purchase.is_equipped = True
    await session.flush()

    return InventoryItemResponse(
        id=purchase.id,
        shop_item=ShopItemResponse(
            id=item.id,
            slug=item.slug,
            name=item.name,
            name_ru=item.name_ru,
            item_type=item.item_type,
            price_coins=item.price_coins,
            required_level=item.required_level,
            sprite_url=item.sprite_url,
            owned=True,
            equipped=True,
        ),
        is_equipped=True,
        purchased_at=purchase.purchased_at.isoformat(),
    )


@router.post("/unequip/{purchase_id}")
async def unequip_item(
    purchase_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Unequip an item."""
    result = await session.execute(
        select(UserPurchase)
        .where(UserPurchase.id == purchase_id)
        .where(UserPurchase.user_id == user.id)
    )
    purchase = result.scalar_one_or_none()

    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in inventory",
        )

    purchase.is_equipped = False
    await session.flush()

    return {"message": "Item unequipped"}
