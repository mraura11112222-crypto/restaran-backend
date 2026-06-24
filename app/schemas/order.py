"""Order-related Pydantic v2 schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    """Single line item when placing an order."""

    menu_item_id: UUID = Field(..., description="Menu item to order")
    quantity: int = Field(..., gt=0, description="Quantity (must be > 0)")
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Special notes for this item",
    )


class OrderCreate(BaseModel):
    """Schema for placing a new order."""

    branch_id: Optional[UUID] = Field(
        default=None, description="Branch to place the order at"
    )
    order_type: str = Field(
        ...,
        pattern=r"^(DINE_IN|DELIVERY|TAKEAWAY)$",
        description="Order type: DINE_IN, DELIVERY, or TAKEAWAY",
    )
    table_number: Optional[int] = Field(
        default=None, ge=1, description="Table number (for DINE_IN)"
    )
    items: List[OrderItemCreate] = Field(
        ..., min_length=1, description="Order line items"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="General order notes",
    )
    delivery_address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Delivery address (for DELIVERY)",
    )
    delivery_latitude: Optional[float] = Field(
        default=None, ge=-90, le=90
    )
    delivery_longitude: Optional[float] = Field(
        default=None, ge=-180, le=180
    )


class OrderUpdate(BaseModel):
    """Schema for updating order status."""

    status: Optional[str] = Field(
        default=None,
        description="New order status",
    )


class OrderItemResponse(BaseModel):
    """Single line item in an order response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    menu_item_id: UUID
    menu_item_name: str = Field(..., description="Denormalised item name")
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Full order detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    restaurant_id: UUID
    branch_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    status: str
    order_type: str
    table_number: Optional[int] = None
    total_amount: Decimal
    notes: Optional[str] = None
    items: List[OrderItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderListResponse(BaseModel):
    """Lightweight order summary for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    status: str
    order_type: str
    total_amount: Decimal
    items_count: int = Field(
        default=0, description="Number of line items"
    )
    created_at: datetime
