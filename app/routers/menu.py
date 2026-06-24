"""
Menu router — CRUD for categories and menu items with image/video support.
"""

import uuid
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.core.exceptions import NotFoundException

router = APIRouter()


# ===== CATEGORIES =====

@router.get(
    "/categories",
    summary="Kategoriyalar ro'yxati",
)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Menyu kategoriyalarini ko'rish."""
    from app.models.menu import Category

    result = await db.execute(
        select(Category)
        .where(Category.restaurant_id == current_user.restaurant_id)
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "image_url": c.image_url,
            "sort_order": c.sort_order,
            "is_active": c.is_active,
        }
        for c in categories
    ]


@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    summary="Kategoriya yaratish",
    dependencies=[Depends(allow_admin)],
)
async def create_category(
    name: str,
    description: Optional[str] = None,
    sort_order: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Yangi menyu kategoriyasi yaratish."""
    from app.models.menu import Category

    category = Category(
        id=uuid.uuid4(),
        restaurant_id=current_user.restaurant_id,
        name=name,
        description=description,
        sort_order=sort_order,
        is_active=True,
    )
    db.add(category)
    await db.flush()
    return {"id": str(category.id), "name": category.name, "message": "Kategoriya yaratildi"}


@router.patch(
    "/categories/{category_id}",
    summary="Kategoriya tahrirlash",
    dependencies=[Depends(allow_admin)],
)
async def update_category(
    category_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Kategoriyani tahrirlash."""
    from app.models.menu import Category

    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.restaurant_id == current_user.restaurant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundException("Kategoriya topilmadi")

    if name is not None:
        category.name = name
    if description is not None:
        category.description = description
    if sort_order is not None:
        category.sort_order = sort_order
    if is_active is not None:
        category.is_active = is_active

    await db.flush()
    return {"message": "Kategoriya yangilandi"}


@router.delete(
    "/categories/{category_id}",
    summary="Kategoriya o'chirish",
    dependencies=[Depends(allow_admin)],
)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Kategoriyani o'chirish."""
    from app.models.menu import Category

    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.restaurant_id == current_user.restaurant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundException("Kategoriya topilmadi")

    await db.delete(category)
    await db.flush()
    return {"message": "Kategoriya o'chirildi"}


# ===== MENU ITEMS =====

@router.get(
    "/items",
    summary="Menyu elementlari",
)
async def get_menu_items(
    category_id: Optional[uuid.UUID] = None,
    available_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Menyu elementlarini ko'rish (filter bilan)."""
    from app.models.menu import MenuItem

    query = select(MenuItem).where(MenuItem.restaurant_id == current_user.restaurant_id)

    if category_id:
        query = query.where(MenuItem.category_id == category_id)
    if available_only:
        query = query.where(MenuItem.is_available == True)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(MenuItem.sort_order, MenuItem.name)
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": str(i.id),
                "category_id": str(i.category_id),
                "name": i.name,
                "description": i.description,
                "price": float(i.price),
                "image_url": i.image_url,
                "video_url": i.video_url,
                "is_available": i.is_available,
                "preparation_time": i.preparation_time,
                "sort_order": i.sort_order,
            }
            for i in items
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post(
    "/items",
    status_code=status.HTTP_201_CREATED,
    summary="Menyu element yaratish",
    dependencies=[Depends(allow_admin)],
)
async def create_menu_item(
    category_id: uuid.UUID,
    name: str,
    price: float,
    description: Optional[str] = None,
    preparation_time: Optional[int] = None,
    sort_order: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Yangi menyu elementi (taom) yaratish."""
    from app.models.menu import MenuItem
    from datetime import datetime

    item = MenuItem(
        id=uuid.uuid4(),
        category_id=category_id,
        restaurant_id=current_user.restaurant_id,
        name=name,
        description=description,
        price=price,
        is_available=True,
        preparation_time=preparation_time,
        sort_order=sort_order,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    await db.flush()
    return {"id": str(item.id), "name": item.name, "price": float(item.price), "message": "Menyu element yaratildi"}


@router.patch(
    "/items/{item_id}",
    summary="Menyu element tahrirlash",
    dependencies=[Depends(allow_admin)],
)
async def update_menu_item(
    item_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    price: Optional[float] = None,
    is_available: Optional[bool] = None,
    preparation_time: Optional[int] = None,
    sort_order: Optional[int] = None,
    category_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Menyu elementini tahrirlash."""
    from app.models.menu import MenuItem
    from datetime import datetime

    result = await db.execute(
        select(MenuItem).where(
            MenuItem.id == item_id,
            MenuItem.restaurant_id == current_user.restaurant_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Menyu element topilmadi")

    if name is not None:
        item.name = name
    if description is not None:
        item.description = description
    if price is not None:
        item.price = price
    if is_available is not None:
        item.is_available = is_available
    if preparation_time is not None:
        item.preparation_time = preparation_time
    if sort_order is not None:
        item.sort_order = sort_order
    if category_id is not None:
        item.category_id = category_id

    item.updated_at = datetime.utcnow()
    await db.flush()
    return {"message": "Menyu element yangilandi"}


@router.delete(
    "/items/{item_id}",
    summary="Menyu element o'chirish",
    dependencies=[Depends(allow_admin)],
)
async def delete_menu_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Menyu elementini o'chirish."""
    from app.models.menu import MenuItem

    result = await db.execute(
        select(MenuItem).where(
            MenuItem.id == item_id,
            MenuItem.restaurant_id == current_user.restaurant_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Menyu element topilmadi")

    await db.delete(item)
    await db.flush()
    return {"message": "Menyu element o'chirildi"}
