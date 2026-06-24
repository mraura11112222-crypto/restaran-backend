"""
Admin router — order management, customers, tables, courier assignment.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.schemas.common import MessageResponse
from app.services.order_service import OrderService
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get(
    "/orders",
    summary="Barcha buyurtmalar",
    dependencies=[Depends(allow_admin)],
)
async def get_all_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Barcha buyurtmalarni ko'rish (filter bilan)."""
    service = OrderService(db)
    return await service.get_orders(
        restaurant_id=current_user.restaurant_id,
        status=status_filter,
        page=page,
        per_page=per_page,
    )


@router.patch(
    "/orders/{order_id}/accept",
    summary="Buyurtma qabul qilish",
    dependencies=[Depends(allow_admin)],
)
async def accept_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Kutilayotgan buyurtmani qabul qilish."""
    service = OrderService(db)
    order = await service.update_order_status(order_id, "CONFIRMED", current_user.restaurant_id)

    # Notify customer
    notif_service = NotificationService(db)
    await notif_service.notify_order_status(order.customer_id, order.order_number, "CONFIRMED")

    return {"message": "Buyurtma qabul qilindi", "order_number": order.order_number}


@router.patch(
    "/orders/{order_id}/reject",
    summary="Buyurtma rad etish",
    dependencies=[Depends(allow_admin)],
)
async def reject_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtmani bekor qilish."""
    service = OrderService(db)
    order = await service.update_order_status(order_id, "CANCELLED", current_user.restaurant_id)

    notif_service = NotificationService(db)
    await notif_service.notify_order_status(order.customer_id, order.order_number, "CANCELLED")

    return {"message": "Buyurtma bekor qilindi", "order_number": order.order_number}


@router.post(
    "/orders/{order_id}/assign-courier",
    summary="Kuryer tayinlash",
    dependencies=[Depends(allow_admin)],
)
async def assign_courier(
    order_id: uuid.UUID,
    courier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Buyurtmaga kuryer tayinlash."""
    from app.models.delivery import Delivery, DeliveryStatus
    from app.models.order import Order

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Buyurtma topilmadi")

    # Check existing delivery
    del_result = await db.execute(select(Delivery).where(Delivery.order_id == order_id))
    delivery = del_result.scalar_one_or_none()

    if delivery:
        delivery.courier_id = courier_id
        delivery.status = DeliveryStatus.ASSIGNED
    else:
        delivery = Delivery(
            id=uuid.uuid4(),
            order_id=order_id,
            courier_id=courier_id,
            address="",
            status=DeliveryStatus.ASSIGNED,
        )
        db.add(delivery)

    await db.flush()
    return {"message": "Kuryer tayinlandi", "courier_id": str(courier_id)}


# --- Customer Management ---
@router.get(
    "/customers",
    summary="Mijozlar ro'yxati",
    dependencies=[Depends(allow_admin)],
)
async def get_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran mijozlarini ko'rish."""
    from app.models.user import User, UserRole

    query = select(User).where(
        User.restaurant_id == current_user.restaurant_id,
        User.role == UserRole.CUSTOMER,
    )

    if search:
        query = query.where(
            User.full_name.ilike(f"%{search}%") | User.phone.ilike(f"%{search}%")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "phone": u.phone,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post(
    "/notifications/send",
    summary="Xabar yuborish",
    dependencies=[Depends(allow_admin)],
)
async def send_notification(
    user_id: uuid.UUID,
    title: str,
    message: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Foydalanuvchiga bildirishnoma yuborish."""
    service = NotificationService(db)
    notification = await service.create_notification(user_id, title, message)
    return {"message": "Bildirishnoma yuborildi", "id": str(notification.id)}

@router.patch(
    "/employees/{user_id}/approve",
    response_model=MessageResponse,
    summary="Xodimni tasdiqlash",
)
async def approve_employee(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_active_user),
):
    """Admin orqali xodim (is_active=False) ni tasdiqlash (is_active=True)."""
    current_role = getattr(current_admin.role, "value", current_admin.role)
    if current_role not in ["ADMIN", "BOSS", "SUPER_ADMIN"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")
        
    from app.models.user import User
    from sqlalchemy import select
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
        
    user.is_active = True
    await db.commit()
    return {"message": "Xodim tasdiqlandi va tizimga kirishga ruxsat berildi"}

@router.get("/dashboard", summary="Admin dashboard", dependencies=[Depends(allow_admin)])
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    return {
        "stats": {
            "total_orders": 145,
            "active_tables": 12,
            "total_revenue": 12500000,
            "active_employees": 24
        },
        "recent_orders": [
            { "id": "1", "order_number": "#1042", "status": "PENDING", "total": 125000 },
            { "id": "2", "order_number": "#1043", "status": "PREPARING", "total": 85000 }
        ]
    }

@router.get("/employees", summary="Xodimlar ro'yxati", dependencies=[Depends(allow_admin)])
async def get_employees(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Current restaurant staff and pending staff registrations."""
    from app.models.user import User, UserRole

    result = await db.execute(
        select(User)
        .where(
            User.restaurant_id == current_user.restaurant_id,
            User.role != UserRole.CUSTOMER,
        )
        .order_by(User.is_active.asc(), User.created_at.desc())
    )
    employees = result.scalars().all()

    return [
        {
            "id": str(user.id),
            "full_name": user.full_name,
            "username": user.username,
            "phone": user.phone,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in employees
    ]


class EmployeeCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    username: Optional[str] = None
    password: str
    role: str


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/employees", summary="Xodim yaratish", dependencies=[Depends(allow_admin)])
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    from app.core.exceptions import BadRequestException, ConflictException
    from app.core.security import get_password_hash
    from app.models.user import User, UserRole

    try:
        role = UserRole[data.role.upper()]
    except KeyError:
        raise BadRequestException("Bunday rol mavjud emas")

    if role == UserRole.CUSTOMER:
        raise BadRequestException("Bu sahifadan faqat xodim rollari yaratiladi")

    if data.username:
        existing_username = await db.execute(select(User).where(User.username == data.username))
        if existing_username.scalar_one_or_none():
            raise ConflictException("Bu username allaqachon band")

    if data.phone:
        existing_phone = await db.execute(
            select(User).where(User.phone == data.phone, User.restaurant_id == current_user.restaurant_id)
        )
        if existing_phone.scalar_one_or_none():
            raise ConflictException("Bu telefon allaqachon band")

    user = User(
        id=uuid.uuid4(),
        restaurant_id=current_user.restaurant_id,
        full_name=data.full_name,
        phone=data.phone,
        username=data.username,
        password_hash=get_password_hash(data.password),
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()
    return {"message": "Xodim yaratildi", "id": str(user.id)}


@router.patch("/employees/{user_id}", summary="Xodimni yangilash", dependencies=[Depends(allow_admin)])
async def update_employee(
    user_id: uuid.UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
    from app.core.security import get_password_hash
    from app.models.user import User, UserRole

    result = await db.execute(
        select(User).where(User.id == user_id, User.restaurant_id == current_user.restaurant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("Xodim topilmadi")

    if data.role is not None:
        try:
            role = UserRole[data.role.upper()]
        except KeyError:
            raise BadRequestException("Bunday rol mavjud emas")
        if role == UserRole.CUSTOMER:
            raise BadRequestException("Xodim roli CUSTOMER bo'lishi mumkin emas")
        user.role = role

    if data.username is not None and data.username != user.username:
        existing_username = await db.execute(select(User).where(User.username == data.username))
        if existing_username.scalar_one_or_none():
            raise ConflictException("Bu username allaqachon band")
        user.username = data.username

    if data.phone is not None:
        user.phone = data.phone
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.password:
        user.password_hash = get_password_hash(data.password)
    if data.is_active is not None:
        user.is_active = data.is_active
    user.updated_at = datetime.utcnow()

    await db.flush()
    return {"message": "Xodim yangilandi"}
