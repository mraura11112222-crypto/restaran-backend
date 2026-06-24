"""
Cashier router — payment acceptance, receipts, daily reports, refunds.
"""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_cashier
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService

router = APIRouter()


@router.post(
    "/payments/accept",
    summary="To'lov qabul qilish",
    dependencies=[Depends(allow_cashier)],
)
async def accept_payment(
    order_id: uuid.UUID,
    payment_method: str = "CASH",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtma uchun to'lovni qabul qilish."""
    service = PaymentService(db)
    payment = await service.create_payment(
        order_id=order_id,
        payment_method=payment_method,
        restaurant_id=current_user.restaurant_id,
    )
    return {
        "id": str(payment.id),
        "amount": float(payment.amount),
        "method": payment.payment_method.value,
        "status": payment.status.value,
        "transaction_id": payment.transaction_id,
    }


@router.post(
    "/receipts/{order_id}",
    summary="Chek chiqarish",
    dependencies=[Depends(allow_cashier)],
)
async def generate_receipt(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtma uchun chek ma'lumotlarini qaytarish."""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, current_user.restaurant_id)

    from app.models.payment import Payment
    from sqlalchemy import select

    pay_result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    payment = pay_result.scalar_one_or_none()

    return {
        "receipt": {
            "order_number": order.order_number,
            "date": order.created_at.isoformat() if order.created_at else None,
            "items": [
                {
                    "name": item.menu_item_id,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total": float(item.total_price),
                }
                for item in order.items
            ],
            "total_amount": float(order.total_amount),
            "payment_method": payment.payment_method.value if payment else "N/A",
            "payment_status": payment.status.value if payment else "N/A",
            "transaction_id": payment.transaction_id if payment else None,
        }
    }


@router.post(
    "/orders/{order_id}/cancel",
    summary="Buyurtma bekor / Qaytarish",
    dependencies=[Depends(allow_cashier)],
)
async def cancel_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtmani bekor qilish va to'lovni qaytarish."""
    order_service = OrderService(db)
    order = await order_service.cancel_order(order_id, current_user.restaurant_id)

    # Refund payment if exists
    from app.models.payment import Payment, PaymentStatus
    from sqlalchemy import select

    pay_result = await db.execute(
        select(Payment).where(
            Payment.order_id == order_id,
            Payment.status == PaymentStatus.COMPLETED,
        )
    )
    payment = pay_result.scalar_one_or_none()
    if payment:
        payment_service = PaymentService(db)
        await payment_service.refund_payment(payment.id)

    return {"message": "Buyurtma bekor qilindi va to'lov qaytarildi"}


@router.get(
    "/reports/daily",
    summary="Kunlik hisobot",
    dependencies=[Depends(allow_cashier)],
)
async def get_daily_report(
    report_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Kunlik moliyaviy hisobot."""
    service = PaymentService(db)
    return await service.get_daily_report(current_user.restaurant_id, report_date)


@router.post(
    "/discounts",
    summary="Chegirma qo'llash",
    dependencies=[Depends(allow_cashier)],
)
async def apply_discount(
    order_id: uuid.UUID,
    discount_percent: float = Query(ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtmaga chegirma qo'llash (foiz)."""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, current_user.restaurant_id)

    discount_amount = float(order.total_amount) * (discount_percent / 100)
    order.total_amount = float(order.total_amount) - discount_amount

    from datetime import datetime
    order.updated_at = datetime.utcnow()
    await db.flush()

    return {
        "message": f"{discount_percent}% chegirma qo'llandi",
        "discount_amount": round(discount_amount, 2),
        "new_total": float(order.total_amount),
    }


@router.get(
    "/payments/history",
    summary="To'lov tarixi",
    dependencies=[Depends(allow_cashier)],
)
async def get_payment_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    payment_method: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """To'lov tarixini ko'rish."""
    service = PaymentService(db)
    return await service.get_payment_history(
        restaurant_id=current_user.restaurant_id,
        page=page,
        per_page=per_page,
        payment_method=payment_method,
    )
