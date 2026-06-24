"""User-related Pydantic v2 schemas: auth, registration, staff management."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    """Base fields shared across user schemas."""

    phone: Optional[str] = Field(
        default=None, min_length=9, max_length=20, description="Phone number"
    )
    full_name: str = Field(
        ..., min_length=2, max_length=100, description="Full name"
    )


class UserCreate(UserBase):
    """Schema for creating a new user (customer self-registration)."""

    password: str = Field(
        ..., min_length=6, max_length=128, description="Password"
    )
    role: str = Field(
        default="CUSTOMER",
        description="User role (CUSTOMER by default)",
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile fields (all optional)."""

    full_name: Optional[str] = Field(
        default=None, min_length=2, max_length=100
    )
    phone: Optional[str] = Field(
        default=None, min_length=9, max_length=20
    )
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema returned when reading a user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: Optional[str] = None
    telegram_id: Optional[int] = None
    role: str
    avatar_url: Optional[str] = None
    is_active: bool = True
    restaurant_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    created_at: datetime


class UserLogin(BaseModel):
    """Schema for phone + password login."""

    phone: str = Field(
        ..., min_length=9, max_length=20, description="Phone number"
    )
    password: str = Field(
        ..., min_length=1, max_length=128, description="Password"
    )


class Token(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str = Field(..., description="Subject — usually user ID")
    role: str = Field(..., description="User role")
    restaurant_id: str = Field(
        ..., description="Restaurant ID the user belongs to"
    )
    exp: int = Field(..., description="Expiration timestamp (epoch)")


class StaffCreate(UserCreate):
    """Schema for creating staff members (waiter, chef, manager, etc.).

    Role must NOT be CUSTOMER — validated via field_validator.
    """

    branch_id: Optional[UUID] = Field(
        default=None,
        description="Branch this staff member is assigned to",
    )
    role: str = Field(
        ...,
        description="Staff role (ADMIN, CASHIER, CHEF, BOSS — not CUSTOMER)",
    )

    @field_validator("role")
    @classmethod
    def role_must_not_be_customer(cls, v: str) -> str:
        if v.upper() == "CUSTOMER":
            raise ValueError("Staff role must not be CUSTOMER")
        return v.upper()

class UsernameRegister(BaseModel):
    username: str = Field(..., description="Telegram username or nickname")
    full_name: str = Field(..., description="Full name / Nickname")
    password: str = Field(..., min_length=6, description="Password")
    role: str = Field(default="CUSTOMER", description="User role")
    telegram_code: str = Field(..., min_length=5, max_length=10, description="Code from Telegram bot")

class UsernameLogin(BaseModel):
    username: str = Field(..., description="Telegram username or nickname")
    password: str = Field(..., description="Password")


class TelegramCodeVerify(BaseModel):
    code: str = Field(..., min_length=5, max_length=10, description="Code from Telegram bot")
