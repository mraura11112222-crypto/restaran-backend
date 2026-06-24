"""
Customer router — menu viewing, ordering, payments, reviews.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.menu import MenuItemResponse, CategoryResponse
from app.schemas.common import MessageResponse
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

router = APIRouter()


# --- Menu Viewing ---
@router.get(
    "/menu",
    summary="Menyu ko'rish",
)
async def get_menu(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran menyusini kategoriyalar bilan ko'rish."""
    from app.models.menu import Category, MenuItem
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Category)
        .where(
            Category.restaurant_id == current_user.restaurant_id,
            Category.is_active == True,
        )
        .options(selectinload(Category.items))
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()

    return [
        {
            "id": str(cat.id),
            "name": cat.name,
            "description": cat.description,
            "image_url": cat.image_url,
            "items": [
                {
                    "id": str(item.id),
                    "name": item.name,
                    "description": item.description,
                    "price": float(item.price),
                    "image_url": item.image_url,
                    "video_url": item.video_url,
                    "is_available": item.is_available,
                    "preparation_time": item.preparation_time,
                }
                for item in cat.items
                if item.is_available
            ],
        }
        for cat in categories
    ]


# --- Orders ---
@router.post(
    "/orders",
    status_code=status.HTTP_201_CREATED,
    summary="Buyurtma berish",
)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Yangi buyurtma yaratish."""
    service = OrderService(db)
    order = await service.create_order(data, current_user.id, current_user.restaurant_id)
    return {"id": str(order.id), "order_number": order.order_number, "status": order.status.value, "total_amount": float(order.total_amount)}


@router.get(
    "/orders",
    summary="Mening buyurtmalarim",
)
async def get_my_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Joriy foydalanuvchining buyurtmalari."""
    service = OrderService(db)
    return await service.get_orders(
        restaurant_id=current_user.restaurant_id,
        customer_id=current_user.id,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/orders/{order_id}",
    summary="Buyurtma tafsilotlari",
)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtma tafsilotlarini ko'rish."""
    service = OrderService(db)
    order = await service.get_order(order_id, current_user.restaurant_id)
    return order


# --- Payment ---
@router.post(
    "/orders/{order_id}/pay",
    summary="To'lov qilish",
)
async def pay_order(
    order_id: uuid.UUID,
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtma uchun to'lov qilish (Cash, Click, Payme)."""
    service = PaymentService(db)
    payment = await service.create_payment(
        order_id=order_id,
        payment_method=data.payment_method,
        restaurant_id=current_user.restaurant_id,
    )
    return {
        "id": str(payment.id),
        "amount": float(payment.amount),
        "method": payment.payment_method.value,
        "status": payment.status.value,
        "transaction_id": payment.transaction_id,
    }


# --- Reviews ---
@router.post(
    "/reviews",
    status_code=status.HTTP_201_CREATED,
    summary="Baho berish",
)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtmaga baho va sharh qoldirish."""
    from app.models.review import Review

    review = Review(
        id=uuid.uuid4(),
        order_id=data.order_id,
        customer_id=current_user.id,
        restaurant_id=current_user.restaurant_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.flush()
    return {"id": str(review.id), "rating": review.rating, "message": "Baho qabul qilindi!"}


@router.get("/addresses", summary="Xaridor manzillari")
async def get_addresses(current_user = Depends(get_current_active_user)):
    return [
        { "id": "1", "name": "Uy", "address": "Chilonzor tumani, 5-uy, Toshkent", "lat": 41.2995, "lng": 69.2401, "is_default": True },
        { "id": "2", "name": "Ish", "address": "Yunusobod tumani, 12-uy, Toshkent", "lat": 41.3153, "lng": 69.2817, "is_default": False },
    ]

@router.get("/notifications", summary="Xaridor xabarlari")
async def get_notifications(current_user = Depends(get_current_active_user)):
    return [
        { "id": "1", "type": "order", "title": "Buyurtma tayyor!", "message": "Buyurtma #1234 tayyor.", "is_read": False, "created_at": "2025-01-15 14:30" },
        { "id": "2", "type": "promo", "title": "Yangi promo kod", "message": "Yangi yil uchun 20% chegirma", "is_read": False, "created_at": "2025-01-14 10:00" },
    ]

@router.get("/subscription", summary="Xaridor obunasi")
async def get_subscription(current_user = Depends(get_current_active_user)):
    return {
        "id": "1",
        "plan": "Pro",
        "status": "active",
        "next_billing": "2025-02-15",
        "features": ["Yetkazib berish tekin", "2x bonus ballari", "Maxsus chegirmalar", "Ustuvor xizmat"],
        "price": 85000,
    }

@router.get("/referral/stats", summary="Xaridor referallari")
async def get_referral_stats(current_user = Depends(get_current_active_user)):
    return {
        "total_points": 200,
        "code": "REF" + str(current_user.id)[:6].upper() if hasattr(current_user, 'id') else "REF12345",
        "referrals": [
            { "id": "1", "name": "Alisher K.", "status": "first_order", "created_at": "2025-01-10", "points_earned": 150 },
            { "id": "2", "name": "Malika R.", "status": "registered", "created_at": "2025-01-12", "points_earned": 50 },
        ]
    }
