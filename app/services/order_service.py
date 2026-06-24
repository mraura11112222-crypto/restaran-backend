"""
Order service — order creation, status management, order queries.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException


class OrderService:
    """Handles order CRUD and status transitions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, data, customer_id: uuid.UUID, restaurant_id: uuid.UUID) -> "Order":
        """Create a new order with items."""
        from app.models.order import Order, OrderItem, OrderStatus, OrderType
        from app.models.menu import MenuItem

        # Generate order number
        count_result = await self.db.execute(
            select(func.count(Order.id)).where(Order.restaurant_id == restaurant_id)
        )
        order_count = count_result.scalar() or 0
        order_number = f"ORD-{order_count + 1:06d}"

        # Calculate total and validate items
        total_amount = 0
        order_items = []

        for item_data in data.items:
            result = await self.db.execute(
                select(MenuItem).where(
                    MenuItem.id == item_data.menu_item_id,
                    MenuItem.restaurant_id == restaurant_id,
                    MenuItem.is_available == True,
                )
            )
            menu_item = result.scalar_one_or_none()
            if not menu_item:
                raise BadRequestException(
                    f"Menyu elementi topilmadi yoki mavjud emas: {item_data.menu_item_id}"
                )

            item_total = float(menu_item.price) * item_data.quantity
            total_amount += item_total

            order_items.append(
                OrderItem(
                    id=uuid.uuid4(),
                    menu_item_id=menu_item.id,
                    quantity=item_data.quantity,
                    unit_price=float(menu_item.price),
                    total_price=item_total,
                    notes=getattr(item_data, "notes", None),
                )
            )

        # Create order
        order = Order(
            id=uuid.uuid4(),
            restaurant_id=restaurant_id,
            branch_id=getattr(data, "branch_id", None),
            customer_id=customer_id,
            order_number=order_number,
            table_number=getattr(data, "table_number", None),
            status=OrderStatus.PENDING,
            order_type=OrderType(data.order_type),
            total_amount=total_amount,
            notes=getattr(data, "notes", None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(order)
        await self.db.flush()

        # Add items to order
        for item in order_items:
            item.order_id = order.id
            self.db.add(item)

        await self.db.flush()
        return order

    async def get_order(self, order_id: uuid.UUID, restaurant_id: uuid.UUID) -> "Order":
        """Get order by ID with items loaded."""
        from app.models.order import Order

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.restaurant_id == restaurant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Buyurtma topilmadi")
        return order

    async def get_orders(
        self,
        restaurant_id: uuid.UUID,
        status: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Get paginated orders with optional filters."""
        from app.models.order import Order

        query = select(Order).where(Order.restaurant_id == restaurant_id)

        if status:
            query = query.where(Order.status == status)
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        if branch_id:
            query = query.where(Order.branch_id == branch_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query.options(selectinload(Order.items)))
        orders = result.scalars().all()

        return {
            "items": orders,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    async def update_order_status(
        self, order_id: uuid.UUID, new_status: str, restaurant_id: uuid.UUID
    ) -> "Order":
        """Update order status with validation of transitions."""
        from app.models.order import Order, OrderStatus

        order = await self.get_order(order_id, restaurant_id)

        # Define valid status transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.DELIVERED, OrderStatus.COMPLETED],
            OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: [],
        }

        target_status = OrderStatus(new_status)
        if target_status not in valid_transitions.get(order.status, []):
            raise BadRequestException(
                f"Status o'tish mumkin emas: {order.status.value} -> {new_status}"
            )

        order.status = target_status
        order.updated_at = datetime.utcnow()
        await self.db.flush()
        return order

    async def get_kitchen_orders(self, restaurant_id: uuid.UUID) -> List:
        """Get active orders for kitchen display (Oshpaz)."""
        from app.models.order import Order, OrderStatus

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.restaurant_id == restaurant_id,
                Order.status.in_([
                    OrderStatus.CONFIRMED,
                    OrderStatus.PREPARING,
                ]),
            )
            .order_by(Order.created_at.asc())
        )
        return result.scalars().all()

    async def cancel_order(self, order_id: uuid.UUID, restaurant_id: uuid.UUID) -> "Order":
        """Cancel an order."""
        from app.models.order import OrderStatus

        return await self.update_order_status(order_id, OrderStatus.CANCELLED.value, restaurant_id)
