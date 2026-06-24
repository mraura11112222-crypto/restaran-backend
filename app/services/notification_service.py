"""
Notification service — in-app notifications, SMS sending.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException


class NotificationService:
    """Handles in-app notifications and SMS sending."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str = "SYSTEM",
    ) -> "Notification":
        """Create an in-app notification."""
        from app.models.notification import Notification, NotificationType

        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType(notification_type),
            is_read=False,
            created_at=datetime.utcnow(),
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def notify_order_status(
        self, user_id: uuid.UUID, order_number: str, new_status: str
    ):
        """Send order status notification."""
        status_messages = {
            "CONFIRMED": f"Buyurtma #{order_number} qabul qilindi ✅",
            "PREPARING": f"Buyurtma #{order_number} tayyorlanmoqda 🍳",
            "READY": f"Buyurtma #{order_number} tayyor! 🎉",
            "DELIVERED": f"Buyurtma #{order_number} yetkazildi 🚚",
            "COMPLETED": f"Buyurtma #{order_number} yakunlandi ✨",
            "CANCELLED": f"Buyurtma #{order_number} bekor qilindi ❌",
        }
        message = status_messages.get(new_status, f"Buyurtma #{order_number}: {new_status}")
        return await self.create_notification(
            user_id=user_id,
            title="Buyurtma holati",
            message=message,
            notification_type="ORDER_STATUS",
        )

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Get paginated notifications for a user."""
        from app.models.notification import Notification

        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Mark a notification as read."""
        from app.models.notification import Notification

        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise NotFoundException("Bildirishnoma topilmadi")

        notification.is_read = True
        await self.db.flush()
        return True

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all notifications as read for a user."""
        from app.models.notification import Notification

        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        await self.db.flush()
        return result.rowcount

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread notifications."""
        from app.models.notification import Notification

        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar() or 0
