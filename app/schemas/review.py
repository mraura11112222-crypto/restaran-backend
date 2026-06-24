"""Review / rating Pydantic v2 schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    """Schema for submitting a review."""

    order_id: UUID = Field(..., description="Order being reviewed")
    rating: int = Field(
        ..., ge=1, le=5, description="Rating from 1 to 5"
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional text comment",
    )


class ReviewResponse(BaseModel):
    """Schema returned when reading a review."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    customer_id: UUID
    customer_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime
