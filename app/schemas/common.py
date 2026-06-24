"""Common schemas used across the application."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(
        default=20, ge=1, le=100, description="Items per page"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Usage:
        PaginatedResponse[MenuItemResponse]
    """

    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")


class MessageResponse(BaseModel):
    """Simple message response for operations like delete, update status, etc."""

    message: str
    success: bool = True


class StatisticsResponse(BaseModel):
    """Dashboard / analytics statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_orders: int = Field(default=0, description="Total number of orders")
    total_revenue: Decimal = Field(
        default=Decimal("0"), description="Total revenue"
    )
    total_customers: int = Field(
        default=0, description="Total unique customers"
    )
    avg_order_value: Decimal = Field(
        default=Decimal("0"), description="Average order value"
    )
    top_items: List[Any] = Field(
        default_factory=list, description="Top selling menu items"
    )
    orders_by_status: dict[str, int] = Field(
        default_factory=dict,
        description="Order count grouped by status",
    )
