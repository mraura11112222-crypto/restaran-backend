"""Restaurant & Branch Pydantic v2 schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    """Schema for creating a restaurant."""

    name: str = Field(
        ..., min_length=2, max_length=200, description="Restaurant name"
    )
    phone: str = Field(
        ..., min_length=9, max_length=20, description="Contact phone"
    )
    address: str = Field(
        ..., min_length=5, max_length=300, description="Primary address"
    )
    description: Optional[str] = Field(
        default=None, max_length=1000, description="Short description"
    )


class RestaurantUpdate(BaseModel):
    """Schema for partial restaurant update (all fields optional)."""

    name: Optional[str] = Field(
        default=None, min_length=2, max_length=200
    )
    phone: Optional[str] = Field(
        default=None, min_length=9, max_length=20
    )
    address: Optional[str] = Field(
        default=None, min_length=5, max_length=300
    )
    description: Optional[str] = Field(default=None, max_length=1000)
    logo_url: Optional[str] = Field(default=None, max_length=500)


class RestaurantResponse(BaseModel):
    """Schema returned when reading a restaurant."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    address: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class BranchCreate(BaseModel):
    """Schema for creating a branch under a restaurant."""

    name: str = Field(
        ..., min_length=2, max_length=200, description="Branch name"
    )
    address: str = Field(
        ..., min_length=5, max_length=300, description="Branch address"
    )
    phone: str = Field(
        ..., min_length=9, max_length=20, description="Branch phone"
    )
    latitude: Optional[float] = Field(
        default=None, ge=-90, le=90, description="Latitude"
    )
    longitude: Optional[float] = Field(
        default=None, ge=-180, le=180, description="Longitude"
    )


class BranchResponse(BaseModel):
    """Schema returned when reading a branch."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    address: str
    phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    created_at: datetime


class RestaurantRegister(BaseModel):
    """One-step registration: creates restaurant + admin user."""

    restaurant_name: str = Field(
        ..., min_length=2, max_length=200, description="Restaurant name"
    )
    admin_phone: str = Field(
        ..., min_length=9, max_length=20, description="Admin phone"
    )
    admin_password: str = Field(
        ..., min_length=6, max_length=128, description="Admin password"
    )
    admin_full_name: str = Field(
        ..., min_length=2, max_length=100, description="Admin full name"
    )
