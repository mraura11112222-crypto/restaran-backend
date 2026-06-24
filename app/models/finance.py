"""Finance models - Accounting, Taxes, Currencies."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Boolean,
    Numeric,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class FinancialIntegration(Base):
    """Accounting integrations (1C, QuickBooks)."""
    __tablename__ = "financial_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    system_name = Column(String(100), nullable=False)  # 1C, QUICKBOOKS
    api_credentials = Column(JSON, nullable=True)
    sync_status = Column(String(50), default="ACTIVE")
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant")


class TaxRule(Base):
    """Automated tax calculation rules."""
    __tablename__ = "tax_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
    )
    country_code = Column(String(10), nullable=False)
    tax_name = Column(String(100), nullable=False)  # VAT, NDS
    tax_percentage = Column(Numeric(5, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Currency(Base):
    """Multi-currency support."""
    __tablename__ = "currencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, unique=True)  # USD, UZS, RUB
    symbol = Column(String(10), nullable=True)
    exchange_rate = Column(Numeric(15, 6), nullable=False, default=1.0)
    is_default = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
