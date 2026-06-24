"""Telegram verification code model used by the bot and auth API."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TelegramVerificationCode(Base):
    """Short-lived code generated when a Telegram user presses /start."""

    __tablename__ = "telegram_verification_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), nullable=False, unique=True, index=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    first_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
