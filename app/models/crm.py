"""CRM models - Referral and Social Media."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Integer,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ReferralProgram(Base):
    """Referral management."""
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    referred_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
    )
    referral_code = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), default="PENDING")
    reward_points = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred_user = relationship("User", foreign_keys=[referred_user_id])


class SocialMediaIntegration(Base):
    """Social media connection for users/gamification."""
    __tablename__ = "social_media_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(String(50), nullable=False)  # INSTAGRAM, TIKTOK, FACEBOOK
    social_account_id = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
