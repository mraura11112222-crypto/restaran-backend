"""
Reviews router — Customer reviews and ratings.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin, allow_customer
from app.models.review import Review
from app.models.order import Order
from app.models.user import User

router = APIRouter()


@router.get(
    "/restaurant/{restaurant_id}",
    summary="Restoran sharhlari",
    description="Restoran uchun barcha sharhlar va o'rtacha reyting."
)
async def get_restaurant_reviews(
    restaurant_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Restoran sharhlarini olish."""
    # Get average rating
    avg_query = select(func.avg(Review.rating)).where(Review.restaurant_id == restaurant_id)
    avg_result = await db.execute(avg_query)
    avg_rating = float(avg_result.scalar() or 0)

    # Get reviews with pagination
    query = (
        select(Review, User.full_name, User.phone)
        .join(User, Review.customer_id == User.id)
        .where(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
    )

    count_q = select(func.count()).select_from(
        select(Review).where(Review.restaurant_id == restaurant_id).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    reviews = result.all()

    return {
        "reviews": [
            {
                "id": str(r.Review.id),
                "rating": r.Review.rating,
                "comment": r.Review.comment,
                "customer_name": r.full_name,
                "customer_phone": r.phone,
                "created_at": r.Review.created_at.isoformat() if r.Review.created_at else None,
            }
            for r in reviews
        ],
        "average_rating": round(avg_rating, 1),
        "total_reviews": total,
        "page": page,
        "per_page": per_page,
    }


@router.post(
    "/order/{order_id}",
    summary="Buyurtma uchun sharh qoldirish",
    dependencies=[Depends(allow_customer)],
    status_code=201,
)
async def create_review(
    order_id: uuid.UUID,
    rating: int = Query(..., ge=1, le=5),
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtma yakunlangach mijoz sharh qoldiradi."""
    # Check if order exists and belongs to customer
    order_result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.customer_id == current_user.id,
            Order.status == "DELIVERED",
        )
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi yoki yakunlanmagan")

    # Check if review already exists
    existing = await db.execute(
        select(Review).where(Review.order_id == order_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu buyurtma uchun sharh allaqachon qoldirilgan")

    review = Review(
        order_id=order_id,
        customer_id=current_user.id,
        restaurant_id=order.restaurant_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return {
        "id": str(review.id),
        "rating": review.rating,
        "comment": review.comment,
        "message": "Sharh muvaffaqiyatli qoldirildi",
    }


@router.get(
    "/my",
    summary="Mening sharhlarim",
    dependencies=[Depends(allow_customer)],
)
async def get_my_reviews(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Mijozning o'zi qoldirgan sharhlar."""
    result = await db.execute(
        select(Review).where(Review.customer_id == current_user.id).order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "rating": r.rating,
            "comment": r.comment,
            "order_id": str(r.order_id),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reviews
    ]


@router.delete(
    "/{review_id}",
    summary="Sharhni o'chirish",
    dependencies=[Depends(allow_admin)],
)
async def delete_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Admin sharhni o'chirishi mumkin."""
    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.restaurant_id == current_user.restaurant_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Sharh topilmadi")

    await db.delete(review)
    await db.commit()
    return {"message": "Sharh o'chirildi"}