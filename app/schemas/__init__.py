"""Pydantic v2 schemas for the restaurant management platform.

Import everything here so consumers can do:
    from app.schemas import UserResponse, OrderCreate, ...
"""

from app.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
    StatisticsResponse,
)
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryUpdate,
)
from app.schemas.media import MediaListResponse, MediaUploadResponse
from app.schemas.menu import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
)
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.schemas.payment import (
    DailyReportResponse,
    PaymentCreate,
    PaymentResponse,
)
from app.schemas.restaurant import (
    BranchCreate,
    BranchResponse,
    RestaurantCreate,
    RestaurantRegister,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.user import (
    StaffCreate,
    Token,
    TokenPayload,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # common
    "PaginationParams",
    "PaginatedResponse",
    "MessageResponse",
    "StatisticsResponse",
    # user
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    "StaffCreate",
    # restaurant
    "RestaurantCreate",
    "RestaurantUpdate",
    "RestaurantResponse",
    "BranchCreate",
    "BranchResponse",
    "RestaurantRegister",
    # menu
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "MenuItemCreate",
    "MenuItemUpdate",
    "MenuItemResponse",
    # order
    "OrderItemCreate",
    "OrderCreate",
    "OrderUpdate",
    "OrderItemResponse",
    "OrderResponse",
    "OrderListResponse",
    # payment
    "PaymentCreate",
    "PaymentResponse",
    "DailyReportResponse",
    # delivery
    "DeliveryCreate",
    "DeliveryUpdate",
    "DeliveryResponse",
    # review
    "ReviewCreate",
    "ReviewResponse",
    # media
    "MediaUploadResponse",
    "MediaListResponse",
]
