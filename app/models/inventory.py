"""Inventory models – real-time inventory, suppliers, and transactions."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TransactionType(str, enum.Enum):
    """Тип транзакции инвентаря."""

    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"
    SPOILAGE = "SPOILAGE"


class Supplier(Base):
    """Supplier of ingredients/items."""

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    inventory_items = relationship("InventoryItem", back_populates="supplier")

    def __repr__(self) -> str:
        return f"<Supplier {self.name!r}>"


class InventoryItem(Base):
    """Item in the inventory (ingredient or product)."""

    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=False, comment="e.g. kg, liter, pcs")
    quantity = Column(Float, nullable=False, default=0.0)
    min_quantity = Column(Float, nullable=False, default=0.0, comment="For auto-replenishment alerts")
    cost_per_unit = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    supplier = relationship("Supplier", back_populates="inventory_items")
    transactions = relationship("InventoryTransaction", back_populates="item")

    def __repr__(self) -> str:
        return f"<InventoryItem {self.name!r} qty={self.quantity}>"


class InventoryTransaction(Base):
    """Log of inventory changes."""

    __tablename__ = "inventory_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type = Column(
        SAEnum(TransactionType, name="inventory_transaction_type", create_constraint=True),
        nullable=False,
    )
    quantity = Column(Float, nullable=False, comment="Positive for IN, Negative for OUT")
    reference_id = Column(UUID(as_uuid=True), nullable=True, comment="Can be Order ID or Purchase ID")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    item = relationship("InventoryItem", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<InventoryTransaction {self.transaction_type} qty={self.quantity}>"
