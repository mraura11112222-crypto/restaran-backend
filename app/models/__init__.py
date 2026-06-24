"""
Models package – импортирует все модели, чтобы Alembic и SQLAlchemy
могли обнаружить их через ``Base.metadata``.
"""

# --- Enums (re-export for convenient access) ---
from app.models.user import User, UserRole  # noqa: F401
from app.models.telegram_verification import TelegramVerificationCode  # noqa: F401
from app.models.menu import Category, MenuItem, Recipe, RecipeIngredient  # noqa: F401
from app.models.restaurant import Restaurant, Branch, Table  # noqa: F401
from app.models.order import Order, OrderItem, OrderStatus, OrderType  # noqa: F401
from app.models.payment import Payment, PaymentMethod, PaymentStatus  # noqa: F401
from app.models.wallet import Wallet, WalletTransaction, WalletTransactionStatus  # noqa: F401
from app.models.delivery import Delivery, DeliveryStatus  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
from app.models.bonus import BonusCard, BonusLevel, PromoCode  # noqa: F401
from app.models.media import Media, MediaType  # noqa: F401
from app.models.inventory import Supplier, InventoryItem, InventoryTransaction, TransactionType  # noqa: F401
from app.models.hr import WorkSchedule, StaffPerformance, PerformanceType, Payroll  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.analytics import MarketTrend, CompetitorData, InvestorReport, CustomerSegment  # noqa: F401
from app.models.fleet import DeliveryFleet, DeliveryRoute  # noqa: F401
from app.models.iot import KitchenIoTDevice  # noqa: F401
from app.models.settings import GlobalTenantSetting, IntegrationConfig  # noqa: F401
from app.models.support import SupportTicket  # noqa: F401
from app.models.crm import ReferralProgram, SocialMediaIntegration  # noqa: F401
from app.models.finance import FinancialIntegration, TaxRule, Currency  # noqa: F401
from app.models.hr_extended import SkillMatrix, StaffTraining, RecruitmentCandidate  # noqa: F401

__all__ = [
    # Core
    "User",
    "UserRole",
    "TelegramVerificationCode",
    "Restaurant",
    "Branch",
    "Table",
    # Menu
    "Category",
    "MenuItem",
    "Recipe",
    "RecipeIngredient",
    # Orders
    "Order",
    "OrderItem",
    "OrderStatus",
    "OrderType",
    # Payments
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    # Delivery
    "Delivery",
    "DeliveryStatus",
    # Reviews
    "Review",
    # Notifications
    "Notification",
    "NotificationType",
    # Loyalty
    "BonusCard",
    "BonusLevel",
    "PromoCode",
    # Media
    "Media",
    "MediaType",
    # Inventory
    "Supplier",
    "InventoryItem",
    "InventoryTransaction",
    "TransactionType",
    # HR
    "WorkSchedule",
    "StaffPerformance",
    "PerformanceType",
    "Payroll",
    # Audit
    "AuditLog",
    # Analytics
    "MarketTrend",
    "CompetitorData",
    "InvestorReport",
    "CustomerSegment",
    # Fleet
    "DeliveryFleet",
    "DeliveryRoute",
    # IoT
    "KitchenIoTDevice",
    # Settings
    "GlobalTenantSetting",
    "IntegrationConfig",
    "SupportTicket",
    # CRM
    "ReferralProgram",
    "SocialMediaIntegration",
    # Finance
    "FinancialIntegration",
    "TaxRule",
    "Currency",
    # HR Extended
    "SkillMatrix",
    "StaffTraining",
    "RecruitmentCandidate",
]
