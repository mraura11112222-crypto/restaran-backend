"""Order models – заказы и позиции заказов."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    """Жизненный цикл заказа."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderType(str, enum.Enum):
    """Тип заказа."""

    DINE_IN = "DINE_IN"
    DELIVERY = "DELIVERY"
    TAKEAWAY = "TAKEAWAY"
    DRONE = "DRONE"


class Order(Base):
    """Customer order (заказ)."""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    table_number = Column(String(20), nullable=True)
    status = Column(
        SAEnum(OrderStatus, name="order_status", create_constraint=True),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    order_type = Column(
        SAEnum(OrderType, name="order_type", create_constraint=True),
        nullable=False,
        default=OrderType.DINE_IN,
    )
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    queue_number = Column(Integer, nullable=True, comment="Real-time navbat raqami")
    is_group_order = Column(Boolean, default=False, comment="Is this a group/split bill order")
    parent_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    restaurant = relationship("Restaurant", back_populates="orders")
    branch = relationship("Branch", back_populates="orders")
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)
    delivery = relationship("Delivery", back_populates="order", uselist=False)
    review = relationship("Review", back_populates="order", uselist=False)

    def __repr__(self) -> str:
        return f"<Order {self.order_number!r} status={self.status}>"


class OrderItem(Base):
    """Single line-item inside an order (позиция заказа)."""

    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text, nullable=True)

    # --- Relationships ---
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem qty={self.quantity} total={self.total_price}>"
