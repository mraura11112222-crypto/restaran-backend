"""Notification model – уведомления пользователей."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationType(str, enum.Enum):
    """Тип уведомления."""

    ORDER_STATUS = "ORDER_STATUS"
    PAYMENT = "PAYMENT"
    SYSTEM = "SYSTEM"
    PROMOTION = "PROMOTION"


class Notification(Base):
    """Push / in-app notification sent to a user."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        SAEnum(NotificationType, name="notification_type", create_constraint=True),
        nullable=False,
    )
    channels = Column(JSON, default=list, comment='Sent channels: ["PUSH", "SMS", "WHATSAPP"]')
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.title!r} read={self.is_read}>"
