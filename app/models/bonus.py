"""Bonus & Promo models – бонусные карты и промокоды."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BonusLevel(str, enum.Enum):
    """Уровень бонусной карты."""

    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class BonusCard(Base):
    """Loyalty bonus card for a customer within a restaurant."""

    __tablename__ = "bonus_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    points = Column(Integer, default=0, nullable=False)
    xp_points = Column(Integer, default=0, nullable=False, comment="Gamification XP points")
    level = Column(
        SAEnum(BonusLevel, name="bonus_level", create_constraint=True),
        nullable=False,
        default=BonusLevel.BRONZE,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    customer = relationship("User", back_populates="bonus_card")
    restaurant = relationship("Restaurant", back_populates="bonus_cards")

    def __repr__(self) -> str:
        return f"<BonusCard level={self.level} points={self.points}>"


class PromoCode(Base):
    """Promotional discount code (промокод)."""

    __tablename__ = "promo_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), nullable=False, unique=True, index=True)
    discount_percent = Column(Numeric(5, 2), nullable=True)
    discount_amount = Column(Numeric(10, 2), nullable=True)
    min_order_amount = Column(Numeric(10, 2), nullable=True)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # --- Relationships ---
    restaurant = relationship("Restaurant", back_populates="promo_codes")

    def __repr__(self) -> str:
        return f"<PromoCode {self.code!r} active={self.is_active}>"
