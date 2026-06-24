"""Menu-related Pydantic v2 schemas: categories and menu items."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Category schemas
# ---------------------------------------------------------------------------


class CategoryCreate(BaseModel):
    """Schema for creating a menu category."""

    name: str = Field(
        ..., min_length=2, max_length=100, description="Category name"
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="Category description"
    )
    sort_order: int = Field(
        default=0, ge=0, description="Display order"
    )


class CategoryUpdate(BaseModel):
    """Schema for partial category update."""

    name: Optional[str] = Field(
        default=None, min_length=2, max_length=100
    )
    description: Optional[str] = Field(default=None, max_length=500)
    sort_order: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Schema returned when reading a category."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    items_count: Optional[int] = Field(
        default=None,
        description="Number of menu items in this category",
    )


# ---------------------------------------------------------------------------
# MenuItem schemas
# ---------------------------------------------------------------------------


class MenuItemCreate(BaseModel):
    """Schema for creating a menu item."""

    category_id: UUID = Field(..., description="Parent category ID")
    name: str = Field(
        ..., min_length=2, max_length=200, description="Item name"
    )
    description: Optional[str] = Field(
        default=None, max_length=1000, description="Item description"
    )
    price: Decimal = Field(
        ..., gt=0, max_digits=12, decimal_places=2, description="Price"
    )
    preparation_time: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated preparation time in minutes",
    )
    sort_order: int = Field(
        default=0, ge=0, description="Display order inside category"
    )


class MenuItemUpdate(BaseModel):
    """Schema for partial menu item update."""

    name: Optional[str] = Field(
        default=None, min_length=2, max_length=200
    )
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[Decimal] = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    image_url: Optional[str] = Field(default=None, max_length=500)
    video_url: Optional[str] = Field(default=None, max_length=500)
    is_available: Optional[bool] = None
    preparation_time: Optional[int] = Field(default=None, ge=1)
    sort_order: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[UUID] = None


class MenuItemResponse(BaseModel):
    """Schema returned when reading a menu item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    name: str
    description: Optional[str] = None
    price: Decimal
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_available: bool = True
    preparation_time: Optional[int] = None
    sort_order: int = 0
    created_at: datetime
