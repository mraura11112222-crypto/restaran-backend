from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class WalletTopupRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., description="CLICK, PAYME, etc.")

class WalletTopupResponse(BaseModel):
    transaction_id: uuid.UUID
    amount: Decimal
    payment_url: str

class WalletTransactionResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    transaction_type: str
    status: str
    payment_method: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class WalletBalanceResponse(BaseModel):
    balance: Decimal
    recent_transactions: list[WalletTransactionResponse]
