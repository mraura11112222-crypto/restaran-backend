"""
Loyalty router — Bonus cards, Promo codes, Rewards.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin, allow_customer
from app.models.bonus import BonusCard, BonusLevel, PromoCode
from app.models.user import User

router = APIRouter()


# --- Bonus Card Endpoints ---

@router.get(
    "/my-card",
    summary="Mening bonus kartam",
    dependencies=[Depends(allow_customer)],
)
async def get_my_bonus_card(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Mijozning bonus kartasi ma'lumotlari."""
    result = await db.execute(
        select(BonusCard).where(BonusCard.customer_id == current_user.id)
    )
    card = result.scalar_one_or_none()

    if not card:
        return {
            "has_card": False,
            "points": 0,
            "xp_points": 0,
            "level": BonusLevel.BRONZE.value,
            "next_level": BonusLevel.SILVER.value,
            "points_to_next": 100,
        }

    # Calculate next level threshold
    level_thresholds = {
        BonusLevel.BRONZE: 100,
        BonusLevel.SILVER: 500,
        BonusLevel.GOLD: 1500,
        BonusLevel.PLATINUM: None,
    }

    current_threshold = level_thresholds.get(card.level, 100)
    next_level = None
    points_to_next = 0

    if card.level == BonusLevel.BRONZE:
        next_level = BonusLevel.SILVER.value
        points_to_next = max(0, 100 - card.points)
    elif card.level == BonusLevel.SILVER:
        next_level = BonusLevel.GOLD.value
        points_to_next = max(0, 500 - card.points)
    elif card.level == BonusLevel.GOLD:
        next_level = BonusLevel.PLATINUM.value
        points_to_next = max(0, 1500 - card.points)

    return {
        "has_card": True,
        "id": str(card.id),
        "points": card.points,
        "xp_points": card.xp_points,
        "level": card.level.value,
        "next_level": next_level,
        "points_to_next": points_to_next,
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }


@router.post(
    "/my-card/earn",
    summary="Ball to'plash",
    dependencies=[Depends(allow_customer)],
    status_code=201,
)
async def earn_points(
    points: int = Query(..., ge=1),
    order_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtma tugagach mijozga ball berish."""
    result = await db.execute(
        select(BonusCard).where(BonusCard.customer_id == current_user.id)
    )
    card = result.scalar_one_or_none()

    if not card:
        # Create new bonus card
        card = BonusCard(
            customer_id=current_user.id,
            restaurant_id=current_user.restaurant_id,
            points=points,
            xp_points=points,
            level=BonusLevel.BRONZE,
        )
        db.add(card)
    else:
        card.points += points
        card.xp_points += points

        # Level up logic
        if card.points >= 1500 and card.level == BonusLevel.GOLD:
            card.level = BonusLevel.PLATINUM
        elif card.points >= 500 and card.level == BonusLevel.SILVER:
            card.level = BonusLevel.GOLD
        elif card.points >= 100 and card.level == BonusLevel.BRONZE:
            card.level = BonusLevel.SILVER

    await db.commit()
    await db.refresh(card)

    return {
        "message": f"{points} ball qo'shildi",
        "total_points": card.points,
        "level": card.level.value,
        "new_level": card.level.value if (card.points >= 100 and card.level != BonusLevel.BRONZE) else None,
    }


@router.post(
    "/my-card/redeem",
    summary="Ballarni ishlatish",
    dependencies=[Depends(allow_customer)],
)
async def redeem_points(
    points: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Ballarni chegirmaga aylantirish."""
    result = await db.execute(
        select(BonusCard).where(BonusCard.customer_id == current_user.id)
    )
    card = result.scalar_one_or_none()

    if not card or card.points < points:
        raise HTTPException(status_code=400, detail="Yetarli ball mavjud emas")

    # Convert points to discount (1 point = 10 so'm)
    discount_amount = points * 10
    card.points -= points
    await db.commit()
    await db.refresh(card)

    return {
        "message": f"{points} ball ishlatildi",
        "discount_amount": discount_amount,
        "remaining_points": card.points,
    }


# --- Promo Code Endpoints ---

@router.get(
    "/promo-codes",
    summary="Promo kodlar ro'yxati",
    dependencies=[Depends(allow_admin)],
)
async def get_promo_codes(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran promo kodlari."""
    result = await db.execute(
        select(PromoCode).where(PromoCode.restaurant_id == current_user.restaurant_id)
    )
    codes = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "code": c.code,
            "discount_percent": float(c.discount_percent) if c.discount_percent else None,
            "discount_amount": float(c.discount_amount) if c.discount_amount else None,
            "min_order_amount": float(c.min_order_amount) if c.min_order_amount else None,
            "max_uses": c.max_uses,
            "current_uses": c.current_uses,
            "is_active": c.is_active,
            "valid_from": c.valid_from.isoformat() if c.valid_from else None,
            "valid_until": c.valid_until.isoformat() if c.valid_until else None,
        }
        for c in codes
    ]


@router.post(
    "/promo-codes",
    summary="Promo kod yaratish",
    dependencies=[Depends(allow_admin)],
    status_code=201,
)
async def create_promo_code(
    code: str,
    discount_percent: Optional[float] = None,
    discount_amount: Optional[float] = None,
    min_order_amount: Optional[float] = None,
    max_uses: Optional[int] = None,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Yangi promo kod yaratish."""
    # Check if code already exists
    existing = await db.execute(
        select(PromoCode).where(PromoCode.code == code.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu kod allaqachon mavjud")

    if not discount_percent and not discount_amount:
        raise HTTPException(status_code=400, detail="Chegirma foizi yoki summasini kiriting")

    promo = PromoCode(
        restaurant_id=current_user.restaurant_id,
        code=code.upper(),
        discount_percent=discount_percent,
        discount_amount=discount_amount,
        min_order_amount=min_order_amount,
        max_uses=max_uses,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)

    return {
        "id": str(promo.id),
        "code": promo.code,
        "message": "Promo kod yaratildi",
    }


@router.post(
    "/promo-codes/validate/{code}",
    summary="Promo kodni tekshirish",
    dependencies=[Depends(allow_customer)],
)
async def validate_promo_code(
    code: str,
    order_amount: float = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Promo kodni tekshirish va chegirma hisoblash."""
    result = await db.execute(
        select(PromoCode).where(
            PromoCode.code == code.upper(),
            PromoCode.restaurant_id == current_user.restaurant_id,
            PromoCode.is_active == True,
        )
    )
    promo = result.scalar_one_or_none()

    if not promo:
        raise HTTPException(status_code=404, detail="Promo kod topilmadi")

    # Check validity period
    now = datetime.utcnow()
    if promo.valid_from and now < promo.valid_from:
        raise HTTPException(status_code=400, detail="Kod hali boshlanmagan")
    if promo.valid_until and now > promo.valid_until:
        raise HTTPException(status_code=400, detail="Kod muddati tugagan")

    # Check usage limit
    if promo.max_uses and promo.current_uses >= promo.max_uses:
        raise HTTPException(status_code=400, detail="Kod ishlatish limiti tugagan")

    # Check minimum order amount
    if promo.min_order_amount and order_amount < float(promo.min_order_amount):
        raise HTTPException(
            status_code=400,
            detail=f"Minimal buyurtma summasi: {promo.min_order_amount}"
        )

    # Calculate discount
    discount = 0
    if promo.discount_percent:
        discount = order_amount * (float(promo.discount_percent) / 100)
    elif promo.discount_amount:
        discount = float(promo.discount_amount)

    return {
        "valid": True,
        "code": promo.code,
        "discount": round(discount, 2),
        "discount_percent": float(promo.discount_percent) if promo.discount_percent else None,
        "final_amount": round(order_amount - discount, 2),
    }


@router.patch(
    "/promo-codes/{promo_id}/deactivate",
    summary="Promo kodni o'chirish",
    dependencies=[Depends(allow_admin)],
)
async def deactivate_promo_code(
    promo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Promo kodni faolsizlantirish."""
    result = await db.execute(
        select(PromoCode).where(
            PromoCode.id == promo_id,
            PromoCode.restaurant_id == current_user.restaurant_id,
        )
    )
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo kod topilmadi")

    promo.is_active = False
    await db.commit()
    return {"message": "Promo kod o'chirildi"}