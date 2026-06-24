"""Audit models – security audit trails."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AuditLog(Base):
    """Audit trail for system changes."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(255), nullable=False, comment="e.g. CREATE_USER, UPDATE_SETTINGS")
    entity_type = Column(String(100), nullable=False, comment="e.g. User, Restaurant, Order")
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    changes = Column(JSON, nullable=True, comment="Before and after state")
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.entity_type}>"
