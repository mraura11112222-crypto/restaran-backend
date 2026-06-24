"""Restaurant and Branch models – заведения и их филиалы."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Restaurant(Base):
    """Top-level restaurant entity."""

    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(String(512), nullable=True)
    logo_url = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    settings = Column(JSON, nullable=True, default=dict)
    virtual_tour_url = Column(String(512), nullable=True, comment="360/VR Virtual Tour URL")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    branches = relationship("Branch", back_populates="restaurant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="restaurant")
    categories = relationship("Category", back_populates="restaurant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")
    reviews = relationship("Review", back_populates="restaurant")
    bonus_cards = relationship("BonusCard", back_populates="restaurant")
    promo_codes = relationship("PromoCode", back_populates="restaurant", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="restaurant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Restaurant {self.name!r}>"


class Branch(Base):
    """Physical branch / location of a restaurant (филиал)."""

    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    address = Column(String(512), nullable=True)
    phone = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    restaurant = relationship("Restaurant", back_populates="branches")
    users = relationship("User", back_populates="branch")
    orders = relationship("Order", back_populates="branch")

    def __repr__(self) -> str:
        return f"<Branch {self.name!r}>"


class Table(Base):
    """Table management for QR and ordering."""
    __tablename__ = "tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    table_number = Column(Integer, nullable=False)
    capacity = Column(Integer, default=4, nullable=False)
    qr_code_url = Column(String(512), nullable=True)
    status = Column(String(50), default="AVAILABLE", nullable=False)  # AVAILABLE, OCCUPIED, RESERVED

    # Relationships
    branch = relationship("Branch", backref="tables")

    def __repr__(self) -> str:
        return f"<Table {self.table_number} at Branch {self.branch_id}>"
