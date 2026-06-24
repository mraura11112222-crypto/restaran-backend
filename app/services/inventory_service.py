"""
Inventory service — auto replenishment, stock management.
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.inventory import InventoryItem, InventoryTransaction, TransactionType
from app.core.exceptions import NotFoundException


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_items(self, restaurant_id: uuid.UUID) -> List[InventoryItem]:
        result = await self.db.execute(
            select(InventoryItem).where(InventoryItem.restaurant_id == restaurant_id)
        )
        return result.scalars().all()

    async def add_stock(
        self, item_id: uuid.UUID, quantity: float, restaurant_id: uuid.UUID, notes: str = ""
    ):
        result = await self.db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.restaurant_id == restaurant_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException("Inventar elementi topilmadi")

        item.quantity += quantity
        item.updated_at = datetime.utcnow()

        txn = InventoryTransaction(
            id=uuid.uuid4(),
            item_id=item.id,
            transaction_type=TransactionType.IN,
            quantity=quantity,
            notes=notes
        )
        self.db.add(txn)
        await self.db.flush()
        return item

    async def use_stock(
        self, item_id: uuid.UUID, quantity: float, restaurant_id: uuid.UUID, reference_id: uuid.UUID = None
    ):
        result = await self.db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.restaurant_id == restaurant_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException("Inventar elementi topilmadi")

        item.quantity -= quantity
        item.updated_at = datetime.utcnow()

        txn = InventoryTransaction(
            id=uuid.uuid4(),
            item_id=item.id,
            transaction_type=TransactionType.OUT,
            quantity=-quantity,
            reference_id=reference_id
        )
        self.db.add(txn)
        await self.db.flush()

        # Check for auto-replenishment alert
        if item.quantity <= item.min_quantity:
            # Here we would trigger an auto-order or alert
            pass

        return item
