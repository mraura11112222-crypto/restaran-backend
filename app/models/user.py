"""User model – сотрудники и клиенты ресторана."""

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
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """Роли пользователей в системе."""

    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
    CASHIER = "CASHIER"
    CHEF = "CHEF"
    BOSS = "BOSS"
    SUPER_ADMIN = "SUPER_ADMIN"


class User(Base):
    """Platform user — customer or staff member."""

    __tablename__ = "users"

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
    telegram_id = Column(BigInteger, nullable=True, index=True)
    username = Column(String(255), nullable=True, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(
        SAEnum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
        default=UserRole.CUSTOMER,
    )
    avatar_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    restaurant = relationship("Restaurant", back_populates="users")
    branch = relationship("Branch", back_populates="users")
    orders = relationship("Order", back_populates="customer", foreign_keys="[Order.customer_id]")
    reviews = relationship("Review", back_populates="customer")
    notifications = relationship("Notification", back_populates="user")
    bonus_card = relationship("BonusCard", back_populates="customer", uselist=False)
    delivery_assignments = relationship(
        "Delivery", back_populates="courier", foreign_keys="[Delivery.courier_id]"
    )
    work_schedules = relationship("WorkSchedule", cascade="all, delete-orphan")
    performances = relationship(
        "StaffPerformance", foreign_keys="[StaffPerformance.user_id]", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Телефон уникален в рамках одного ресторана
        {"comment": "Platform users"},
    )

    def __repr__(self) -> str:
        return f"<User {self.full_name!r} role={self.role}>"
