"""
Chef router — kitchen order management, status updates, availability.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_chef
from app.services.order_service import OrderService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get(
    "/orders",
    summary="Oshxona buyurtmalari",
    dependencies=[Depends(allow_chef)],
)
async def get_kitchen_orders(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Oshpaz uchun faol buyurtmalar — CONFIRMED va PREPARING statusdagilar.
    Eng eski buyurtma birinchi ko'rinadi.
    """
    service = OrderService(db)
    orders = await service.get_kitchen_orders(current_user.restaurant_id)

    return [
        {
            "id": str(o.id),
            "order_number": o.order_number,
            "status": o.status.value,
            "order_type": o.order_type.value,
            "table_number": o.table_number,
            "notes": o.notes,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": [
                {
                    "id": str(item.id),
                    "menu_item_id": str(item.menu_item_id),
                    "quantity": item.quantity,
                    "notes": item.notes,
                }
                for item in o.items
            ],
        }
        for o in orders
    ]


@router.put(
    "/orders/{order_id}/status",
    summary="Buyurtma holatini yangilash (tayyorlash)",
)
async def update_order_status(
    order_id: uuid.UUID,
    new_status: str = Query(..., description="Masalan: PREPARING, READY"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Oshpaz buyurtmani qabul qilishi yoki tayyor qildi deb belgilashi."""
    service = OrderService(db)
    order = await service.update_order_status(
        order_id=order_id,
        new_status=new_status,
        restaurant_id=current_user.restaurant_id,
    )
    return {"id": str(order.id), "status": order.status.value}


@router.get("/iot/devices", summary="IoT Qurilmalar")
async def get_iot_devices(current_user=Depends(get_current_active_user)):
    from datetime import datetime
    return [
        { "id": "1", "name": "Pech #1", "type": "Oven", "status": "online", "temperature": 180, "last_update": datetime.now().isoformat() },
        { "id": "2", "name": "Sovutgich #1", "type": "Fridge", "status": "online", "temperature": 4, "last_update": datetime.now().isoformat() },
        { "id": "3", "name": "Baskul #1", "type": "Scale", "status": "warning", "pressure": 2.5, "last_update": datetime.now().isoformat() },
    ]


@router.patch(
    "/orders/{order_id}/assign-robot",
    summary="Robotga tayinlash",
    dependencies=[Depends(allow_chef)],
)
async def assign_robot(
    order_id: uuid.UUID,
    robot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Robot orqali yetkazib berishga jo'natish."""
    # Placeholder for IoT integration
    return {"message": f"Buyurtma {robot_id} robotiga biriktirildi"}


@router.get("/stats", summary="Oshpaz statistikasi")
async def get_stats(current_user=Depends(get_current_active_user)):
    return {
        "today_orders": 47,
        "today_dishes": 128,
        "avg_prep_time": 12,
        "popular_dishes": [
            { "name": "Osh", "count": 23 },
            { "name": "Manti", "count": 18 },
            { "name": "Lag'mon", "count": 15 },
            { "name": "Sho'rva", "count": 12 }
        ]
    }


@router.patch(
    "/orders/{order_id}/ready",
    summary="Buyurtma tayyor",
    dependencies=[Depends(allow_chef)],
)
async def mark_order_ready(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtmani READY deb belgilash."""
    service = OrderService(db)
    order = await service.update_order_status(order_id, "READY", current_user.restaurant_id)

    notif_service = NotificationService(db)
    await notif_service.notify_order_status(order.customer_id, order.order_number, "READY")

    return {"message": "Buyurtma tayyor! 🎉", "order_number": order.order_number}


@router.patch(
    "/menu-items/{item_id}/availability",
    summary="Mahsulot mavjudligi",
    dependencies=[Depends(allow_chef)],
)
async def toggle_item_availability(
    item_id: uuid.UUID,
    is_available: bool,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Mahsulotni mavjud/mavjud emas deb belgilash (mahsulot tugadi)."""
    from app.models.menu import MenuItem
    from app.core.exceptions import NotFoundException

    result = await db.execute(
        select(MenuItem).where(
            MenuItem.id == item_id,
            MenuItem.restaurant_id == current_user.restaurant_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Menyu elementi topilmadi")

    item.is_available = is_available
    await db.flush()

    status_text = "mavjud" if is_available else "tugagan"
    return {"message": f"'{item.name}' — {status_text}", "is_available": is_available}


@router.get(
    "/tasks",
    summary="Vazifalar ro'yxati",
    dependencies=[Depends(allow_chef)],
)
async def get_tasks(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Oshpaz uchun bugungi vazifalar (buyurtma asosida)."""
    from app.models.order import Order, OrderItem, OrderStatus
    from sqlalchemy import func, cast, Date
    from datetime import date

    # Group by menu item for today
    result = await db.execute(
        select(
            OrderItem.menu_item_id,
            func.sum(OrderItem.quantity).label("total_qty"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.restaurant_id == current_user.restaurant_id,
            Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PREPARING]),
            cast(Order.created_at, Date) == date.today(),
        )
        .group_by(OrderItem.menu_item_id)
    )

    return [
        {"menu_item_id": str(row[0]), "total_quantity": int(row[1])}
        for row in result.all()
    ]


@router.get(
    "/schedule",
    summary="Ish jadvali",
    dependencies=[Depends(allow_chef)],
)
async def get_my_schedule(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Joriy foydalanuvchining ish jadvali."""
    # Placeholder — WorkSchedule modeli bo'yicha kengaytiriladi
    return {"message": "Ish jadvali hozircha mavjud emas", "schedules": []}
