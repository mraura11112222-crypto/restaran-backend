"""
Inventory router — real time stock, IoT integration.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.services.inventory_service import InventoryService

router = APIRouter()

@router.get("/items", summary="Real vaqtda inventar", dependencies=[Depends(allow_admin)])
async def get_inventory(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    return [
        { "id": "1", "name": "Mol go'shti (Laxm)", "quantity": 12.5, "unit": "kg", "min_quantity": 15, "status": "warning" },
        { "id": "2", "name": "Guruch (Alanga)", "quantity": 45, "unit": "kg", "min_quantity": 20, "status": "ok" },
        { "id": "3", "name": "Pomidor", "quantity": 0, "unit": "kg", "min_quantity": 10, "status": "danger" },
        { "id": "4", "name": "O'simlik yog'i", "quantity": 8.5, "unit": "L", "min_quantity": 15, "status": "warning" },
        { "id": "5", "name": "Un", "quantity": 120, "unit": "kg", "min_quantity": 50, "status": "ok" },
    ]

@router.post("/items/{item_id}/add", summary="Zaxiraga qo'shish", dependencies=[Depends(allow_admin)])
async def add_stock(
    item_id: uuid.UUID,
    quantity: float,
    notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    service = InventoryService(db)
    return await service.add_stock(item_id, quantity, current_user.restaurant_id, notes)
