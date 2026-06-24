"""Delivery model – доставка заказов."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryStatus(str, enum.Enum):
    """Статус доставки."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Delivery(Base):
    """Delivery details for a delivery-type order."""

    __tablename__ = "deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    courier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    address = Column(String(512), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(
        SAEnum(DeliveryStatus, name="delivery_status", create_constraint=True),
        nullable=False,
        default=DeliveryStatus.PENDING,
    )
    estimated_time = Column(DateTime, nullable=True)
    actual_delivery_time = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    order = relationship("Order", back_populates="delivery")
    courier = relationship("User", back_populates="delivery_assignments", foreign_keys=[courier_id])

    def __repr__(self) -> str:
        return f"<Delivery status={self.status}>"
