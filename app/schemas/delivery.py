"""Delivery-related Pydantic v2 schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeliveryCreate(BaseModel):
    """Schema for creating a delivery record."""

    order_id: UUID = Field(..., description="Associated order ID")
    address: str = Field(
        ..., min_length=5, max_length=500, description="Delivery address"
    )
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude"
    )


class DeliveryUpdate(BaseModel):
    """Schema for updating delivery status / assignment."""

    status: Optional[str] = Field(
        default=None, description="New delivery status"
    )
    courier_id: Optional[UUID] = Field(
        default=None, description="Assigned courier ID"
    )
    estimated_time: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated delivery time in minutes",
    )


class DeliveryResponse(BaseModel):
    """Schema returned when reading a delivery."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    courier_id: Optional[UUID] = None
    courier_name: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    status: str
    estimated_time: Optional[int] = None
    actual_delivery_time: Optional[datetime] = None
    created_at: datetime
