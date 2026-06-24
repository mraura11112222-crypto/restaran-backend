"""IoT integration models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class KitchenIoTDevice(Base):
    """Smart kitchen appliances (fridges, ovens)."""
    __tablename__ = "kitchen_iot_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_type = Column(String(100), nullable=False)  # SMART_OVEN, FRIDGE_SENSOR
    device_name = Column(String(255), nullable=False)
    status = Column(String(50), default="ONLINE", nullable=False)
    last_reading = Column(JSON, nullable=True)  # {"temperature": 4.2, "unit": "C"}
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    restaurant = relationship("Restaurant")
