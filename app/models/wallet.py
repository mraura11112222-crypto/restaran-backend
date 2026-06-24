"""Wallet model - for customer account balances and transactions."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TransactionType(str, enum.Enum):
    """Тип транзакции кошелька."""
    DEPOSIT = "DEPOSIT"
    PAYMENT = "PAYMENT"


class WalletTransactionStatus(str, enum.Enum):
    """Статус транзакции кошелька."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Wallet(Base):
    """Foydalanuvchi hamyoni (Wallet) - Hisob balansi."""

    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Wallet balance={self.balance}>"


class WalletTransaction(Base):
    """Hamyon tranzaksiyalari (Tushumlar va Xarajatlar)."""

    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(
        SAEnum(TransactionType, name="wallet_transaction_type", create_constraint=True),
        nullable=False,
    )
    status = Column(
        SAEnum(WalletTransactionStatus, name="wallet_transaction_status", create_constraint=True),
        nullable=False,
        default=WalletTransactionStatus.PENDING,
    )
    payment_method = Column(String(50), nullable=True) # CLICK, PAYME, ORDER_PAYMENT
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    wallet = relationship("Wallet", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<WalletTransaction type={self.transaction_type} amount={self.amount}>"
