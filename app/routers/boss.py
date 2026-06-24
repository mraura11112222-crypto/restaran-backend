"""
Boss router — statistics, staff management, menu CRUD, branches, settings.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_boss
from app.core.exceptions import NotFoundException
from app.services.report_service import ReportService
from app.services.auth_service import AuthService
from sqlalchemy import select, func
from app.models.order import Order
from app.models.user import User
from app.models.restaurant import Branch

router = APIRouter()


# --- Statistics ---
@router.get(
    "/statistics",
    summary="Umumiy statistika",
    dependencies=[Depends(allow_boss)],
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Boss dashboard — umumiy statistika."""
    try:
        # Get total revenue
        revenue_result = await db.execute(
            select(func.sum(Order.total_amount)).where(
                Order.restaurant_id == current_user.restaurant_id,
                Order.status != 'cancelled'
            )
        )
        total_revenue = revenue_result.scalar() or 0
        
        # Get order count
        orders_result = await db.execute(
            select(func.count(Order.id)).where(
                Order.restaurant_id == current_user.restaurant_id,
                Order.status != 'cancelled'
            )
        )
        order_count = orders_result.scalar() or 0
        
        # Get branch count
        branches_result = await db.execute(
            select(func.count(Branch.id)).where(
                Branch.restaurant_id == current_user.restaurant_id
            )
        )
        branch_count = branches_result.scalar() or 0
        
        # Get employee count
        employees_result = await db.execute(
            select(func.count(User.id)).where(
                User.restaurant_id == current_user.restaurant_id,
                User.role.in_(['admin', 'cashier', 'chef'])
            )
        )
        employee_count = employees_result.scalar() or 0
        
        # Get revenue trend (last 6 months)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        trend_result = await db.execute(
            select(
                func.to_char(Order.created_at, 'Mon').label('month'),
                func.sum(Order.total_amount).label('revenue'),
                func.count(Order.id).label('orders')
            )
            .where(
                Order.restaurant_id == current_user.restaurant_id,
                Order.created_at >= start_date,
                Order.status != 'cancelled'
            )
            .group_by(func.to_char(Order.created_at, 'Mon'))
            .order_by(func.min(Order.created_at))
        )
        trend_data = trend_result.fetchall()
        
        months = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
        revenue_trend = []
        for row in trend_data:
            month_name = row.month if row.month in months else 'Yan'
            revenue_trend.append({
                'month': month_name,
                'daromad': float(row.revenue or 0),
                'buyurtmalar': row.orders or 0
            })
        
        # Get branches with stats
        branches_stats_result = await db.execute(
            select(
                Branch.name,
                func.count(Order.id).label('order_count')
            )
            .outerjoin(Order, Order.branch_id == Branch.id)
            .where(Branch.restaurant_id == current_user.restaurant_id)
            .group_by(Branch.id, Branch.name)
        )
        branches_stats = branches_stats_result.fetchall()
        branches = [{'name': b.name, 'order_count': b.order_count or 0} for b in branches_stats]
        
        return {
            'total_revenue': float(total_revenue),
            'order_count': order_count,
            'branch_count': branch_count,
            'employee_count': employee_count,
            'revenue_trend': revenue_trend if revenue_trend else [],
            'branches': branches if branches else [],
        }
    except Exception as e:
        print(f"Error in get_statistics: {e}")
        return {
            'total_revenue': 0,
            'order_count': 0,
            'branch_count': 0,
            'employee_count': 0,
            'revenue_trend': [],
            'branches': [],
        }


@router.get(
    "/finance",
    summary="Daromad / Xarajat",
    dependencies=[Depends(allow_boss)],
)
async def get_finance(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Kunlik daromad grafigi (oxirgi N kun)."""
    service = ReportService(db)
    return await service.get_revenue_by_period(current_user.restaurant_id, days)


@router.get(
    "/top-items",
    summary="Eng ko'p sotilgan",
    dependencies=[Depends(allow_boss)],
)
async def get_top_items(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Eng ko'p sotilgan menyu elementlari."""
    service = ReportService(db)
    return await service.get_top_menu_items(current_user.restaurant_id, limit)


# --- Staff Management ---
@router.get(
    "/staff",
    summary="Xodimlar ro'yxati",
    dependencies=[Depends(allow_boss)],
)
async def get_staff(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Barcha xodimlar ro'yxati."""
    service = ReportService(db)
    staff = await service.get_staff_list(current_user.restaurant_id)
    return [
        {
            "id": str(s.id),
            "phone": s.phone,
            "full_name": s.full_name,
            "role": s.role.value,
            "is_active": s.is_active,
            "branch_id": str(s.branch_id) if s.branch_id else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in staff
    ]


@router.post(
    "/staff",
    status_code=status.HTTP_201_CREATED,
    summary="Xodim qo'shish",
    dependencies=[Depends(allow_boss)],
)
async def create_staff(
    phone: str,
    full_name: str,
    password: str,
    role: str,
    branch_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Yangi xodim yaratish (admin, kassir, oshpaz)."""
    from app.schemas.user import StaffCreate

    data = StaffCreate(
        phone=phone,
        full_name=full_name,
        password=password,
        role=role,
        branch_id=branch_id,
    )
    service = AuthService(db)
    user = await service.create_staff(data, current_user.restaurant_id)
    return {
        "id": str(user.id),
        "phone": user.phone,
        "full_name": user.full_name,
        "role": user.role.value,
        "message": "Xodim muvaffaqiyatli yaratildi",
    }


@router.patch(
    "/staff/{user_id}",
    summary="Xodim tahrirlash",
    dependencies=[Depends(allow_boss)],
)
async def update_staff(
    user_id: uuid.UUID,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    branch_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Xodim ma'lumotlarini yangilash."""
    from app.models.user import User

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.restaurant_id == current_user.restaurant_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("Xodim topilmadi")

    if full_name is not None:
        user.full_name = full_name
    if role is not None:
        from app.models.user import UserRole
        user.role = UserRole(role)
    if is_active is not None:
        user.is_active = is_active
    if branch_id is not None:
        user.branch_id = branch_id

    from datetime import datetime
    user.updated_at = datetime.utcnow()
    await db.flush()

    return {"message": "Xodim yangilandi", "id": str(user.id)}


@router.delete(
    "/staff/{user_id}",
    summary="Xodim o'chirish",
    dependencies=[Depends(allow_boss)],
)
async def delete_staff(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Xodimni o'chirish (deactivate)."""
    from app.models.user import User

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.restaurant_id == current_user.restaurant_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("Xodim topilmadi")

    user.is_active = False
    await db.flush()
    return {"message": "Xodim o'chirildi (deaktivatsiya)"}


# --- Branch Management ---
@router.get(
    "/branches",
    summary="Filiallar",
    dependencies=[Depends(allow_boss)],
)
async def get_branches(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran filiallarini ko'rish."""
    from app.models.restaurant import Branch

    result = await db.execute(
        select(Branch).where(Branch.restaurant_id == current_user.restaurant_id)
    )
    branches = result.scalars().all()
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "address": b.address,
            "phone": b.phone,
            "is_active": b.is_active,
        }
        for b in branches
    ]


@router.post(
    "/branches",
    status_code=status.HTTP_201_CREATED,
    summary="Filial qo'shish",
    dependencies=[Depends(allow_boss)],
)
async def create_branch(
    name: str,
    address: str,
    phone: str = "",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Yangi filial qo'shish."""
    from app.models.restaurant import Branch

    branch = Branch(
        id=uuid.uuid4(),
        restaurant_id=current_user.restaurant_id,
        name=name,
        address=address,
        phone=phone,
        is_active=True,
    )
    db.add(branch)
    await db.flush()
    return {"id": str(branch.id), "name": branch.name, "message": "Filial yaratildi"}


# --- Settings ---
@router.get(
    "/settings",
    summary="Platforma sozlamalari",
    dependencies=[Depends(allow_boss)],
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran sozlamalarini olish."""
    from app.models.restaurant import Restaurant

    result = await db.execute(
        select(Restaurant).where(Restaurant.id == current_user.restaurant_id)
    )
    restaurant = result.scalar_one_or_none()
    return {
        "id": str(restaurant.id),
        "name": restaurant.name,
        "phone": restaurant.phone,
        "address": restaurant.address,
        "logo_url": restaurant.logo_url,
        "description": restaurant.description,
        "settings": restaurant.settings,
    }


@router.patch(
    "/settings",
    summary="Sozlamalarni yangilash",
    dependencies=[Depends(allow_boss)],
)
async def update_settings(
    name: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Restoran sozlamalarini yangilash."""
    from app.models.restaurant import Restaurant

    result = await db.execute(
        select(Restaurant).where(Restaurant.id == current_user.restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if name:
        restaurant.name = name
    if phone:
        restaurant.phone = phone
    if address:
        restaurant.address = address
    if description:
        restaurant.description = description

    from datetime import datetime
    restaurant.updated_at = datetime.utcnow()
    await db.flush()
    return {"message": "Sozlamalar yangilandi"}
