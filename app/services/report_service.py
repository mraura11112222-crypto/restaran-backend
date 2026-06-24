"""
Report service — statistics, analytics for Boss dashboard.
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, cast, Date, desc
from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    """Generates reports and statistics for the Boss role."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self, restaurant_id: uuid.UUID) -> dict:
        """Get overview statistics for the boss dashboard."""
        from app.models.order import Order, OrderStatus
        from app.models.user import User, UserRole
        from app.models.menu import MenuItem

        # Total orders (all time)
        total_orders_q = await self.db.execute(
            select(func.count(Order.id)).where(
                Order.restaurant_id == restaurant_id,
                Order.status != OrderStatus.CANCELLED,
            )
        )
        total_orders = total_orders_q.scalar() or 0

        # Total revenue
        revenue_q = await self.db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.restaurant_id == restaurant_id,
                Order.status == OrderStatus.COMPLETED,
            )
        )
        total_revenue = float(revenue_q.scalar() or 0)

        # Total customers
        customers_q = await self.db.execute(
            select(func.count(User.id)).where(
                User.restaurant_id == restaurant_id,
                User.role == UserRole.CUSTOMER,
            )
        )
        total_customers = customers_q.scalar() or 0

        # Average order value
        avg_q = await self.db.execute(
            select(func.coalesce(func.avg(Order.total_amount), 0)).where(
                Order.restaurant_id == restaurant_id,
                Order.status == OrderStatus.COMPLETED,
            )
        )
        avg_order_value = float(avg_q.scalar() or 0)

        # Today's stats
        today = date.today()
        today_orders_q = await self.db.execute(
            select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_amount), 0),
            ).where(
                Order.restaurant_id == restaurant_id,
                cast(Order.created_at, Date) == today,
                Order.status != OrderStatus.CANCELLED,
            )
        )
        today_row = today_orders_q.one()
        today_orders = today_row[0] or 0
        today_revenue = float(today_row[1] or 0)

        # Active staff count
        staff_q = await self.db.execute(
            select(func.count(User.id)).where(
                User.restaurant_id == restaurant_id,
                User.role != UserRole.CUSTOMER,
                User.is_active == True,
            )
        )
        active_staff = staff_q.scalar() or 0

        # Menu items count
        menu_q = await self.db.execute(
            select(func.count(MenuItem.id)).where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True,
            )
        )
        menu_items_count = menu_q.scalar() or 0

        # Orders by status
        status_q = await self.db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.restaurant_id == restaurant_id)
            .group_by(Order.status)
        )
        orders_by_status = {row[0].value: row[1] for row in status_q.all()}

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "avg_order_value": round(avg_order_value, 2),
            "today_orders": today_orders,
            "today_revenue": today_revenue,
            "active_staff": active_staff,
            "menu_items_count": menu_items_count,
            "orders_by_status": orders_by_status,
        }

    async def get_top_menu_items(
        self, restaurant_id: uuid.UUID, limit: int = 10
    ) -> list:
        """Get most ordered menu items."""
        from app.models.order import OrderItem, Order
        from app.models.menu import MenuItem

        result = await self.db.execute(
            select(
                MenuItem.id,
                MenuItem.name,
                MenuItem.price,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.total_price).label("total_revenue"),
            )
            .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.restaurant_id == restaurant_id)
            .group_by(MenuItem.id, MenuItem.name, MenuItem.price)
            .order_by(desc("total_sold"))
            .limit(limit)
        )

        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "price": float(row[2]),
                "total_sold": int(row[3]),
                "total_revenue": float(row[4]),
            }
            for row in result.all()
        ]

    async def get_revenue_by_period(
        self,
        restaurant_id: uuid.UUID,
        days: int = 30,
    ) -> list:
        """Get daily revenue for the last N days."""
        from app.models.order import Order, OrderStatus

        start_date = date.today() - timedelta(days=days)

        result = await self.db.execute(
            select(
                cast(Order.created_at, Date).label("day"),
                func.count(Order.id).label("orders_count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            )
            .where(
                Order.restaurant_id == restaurant_id,
                cast(Order.created_at, Date) >= start_date,
                Order.status == OrderStatus.COMPLETED,
            )
            .group_by("day")
            .order_by("day")
        )

        return [
            {
                "date": row[0].isoformat(),
                "orders_count": row[1],
                "revenue": float(row[2]),
            }
            for row in result.all()
        ]

    async def get_staff_list(self, restaurant_id: uuid.UUID) -> list:
        """Get all staff members."""
        from app.models.user import User, UserRole

        result = await self.db.execute(
            select(User)
            .where(
                User.restaurant_id == restaurant_id,
                User.role != UserRole.CUSTOMER,
            )
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
