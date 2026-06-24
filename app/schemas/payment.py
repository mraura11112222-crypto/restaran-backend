"""Payment & daily report Pydantic v2 schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    """Schema for initiating a payment."""

    order_id: UUID = Field(..., description="Order to pay for")
    payment_method: str = Field(
        ...,
        pattern=r"^(CASH|CLICK|PAYME|CARD)$",
        description="Payment method: CASH, CLICK, PAYME, or CARD",
    )


class PaymentResponse(BaseModel):
    """Schema returned after payment creation or lookup."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    amount: Decimal
    payment_method: str
    status: str
    transaction_id: Optional[str] = None
    created_at: datetime


class DailyReportResponse(BaseModel):
    """Aggregated financial report for a single day."""

    model_config = ConfigDict(from_attributes=True)

    date: date
    total_orders: int = Field(default=0)
    total_revenue: Decimal = Field(default=Decimal("0"))
    cash_amount: Decimal = Field(default=Decimal("0"))
    card_amount: Decimal = Field(default=Decimal("0"))
    click_amount: Decimal = Field(default=Decimal("0"))
    payme_amount: Decimal = Field(default=Decimal("0"))
    cancelled_orders: int = Field(default=0)
    refunded_amount: Decimal = Field(default=Decimal("0"))
