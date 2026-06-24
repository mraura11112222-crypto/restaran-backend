"""Fleet management models for delivery."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryFleet(Base):
    """Vehicles, drones, and robots in the fleet."""
    __tablename__ = "delivery_fleet"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vehicle_type = Column(String(50), nullable=False)  # CAR, BIKE, DRONE, ROBOT
    license_plate = Column(String(50), nullable=True)
    status = Column(String(50), default="AVAILABLE", nullable=False)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    last_ping = Column(DateTime, default=datetime.utcnow)

    # Relationships
    restaurant = relationship("Restaurant")


class DeliveryRoute(Base):
    """Assigned delivery routes."""
    __tablename__ = "delivery_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fleet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_fleet.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    estimated_arrival = Column(DateTime, nullable=True)
    route_status = Column(String(50), default="PENDING", nullable=False)

    # Relationships
    fleet = relationship("DeliveryFleet")
    order = relationship("Order")
