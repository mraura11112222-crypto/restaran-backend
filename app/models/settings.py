"""Global tenant settings and API configurations."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class GlobalTenantSetting(Base):
    """Firm-level settings and dynamic pricing config."""
    __tablename__ = "global_tenant_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    is_dynamic_pricing_enabled = Column(Boolean, default=False)
    enabled_modules = Column(JSON, default=list)  # ["HR", "INVENTORY", "DELIVERY"]
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    restaurant = relationship("Restaurant")


class IntegrationConfig(Base):
    """API configurations for external services."""
    __tablename__ = "integration_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_name = Column(String(100), nullable=False)  # CLOUDINARY, PAYME, ESKIZ
    api_key = Column(String(255), nullable=True)
    api_secret = Column(String(255), nullable=True)
    webhook_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    restaurant = relationship("Restaurant")
