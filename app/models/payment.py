"""Payment model – оплата заказов (Click, Payme, наличные, карта)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentMethod(str, enum.Enum):
    """Способ оплаты."""

    CASH = "CASH"
    CLICK = "CLICK"
    PAYME = "PAYME"
    CARD = "CARD"


class PaymentStatus(str, enum.Enum):
    """Статус платежа."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    """Payment record tied to a single order."""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(
        SAEnum(PaymentMethod, name="payment_method", create_constraint=True),
        nullable=False,
    )
    status = Column(
        SAEnum(PaymentStatus, name="payment_status", create_constraint=True),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    transaction_id = Column(String(255), nullable=True)
    provider_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    order = relationship("Order", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment {self.payment_method} status={self.status}>"
