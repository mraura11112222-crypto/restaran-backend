"""
Super Admin router — global platform management (Multi-country, Modules, API settings).
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_active_user

# Define a dependency for allow_super_admin.
# Wait, let's just do a mock check here for now.
async def allow_super_admin(current_user=Depends(get_current_active_user)):
    from app.core.exceptions import ForbiddenException
    from app.models.user import UserRole
    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Siz Super Admin emassiz")
    return current_user

router = APIRouter()

@router.get("/restaurants", summary="Global restoranlar ro'yxati", dependencies=[Depends(allow_super_admin)])
async def get_all_restaurants(db: AsyncSession = Depends(get_db)):
    """SaaS platformasidagi barcha restoranlar (Multi-Country)."""
    from app.models.restaurant import Restaurant
    result = await db.execute(select(Restaurant))
    return result.scalars().all()

@router.get("/audit-logs", summary="Global audit loglar", dependencies=[Depends(allow_super_admin)])
async def get_audit_logs(db: AsyncSession = Depends(get_db)):
    """Tizimdagi xavfsizlik o'zgarishlari va loglari."""
    from app.models.audit import AuditLog
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100))
    return result.scalars().all()

@router.get("/api-keys", summary="Global API Keys", dependencies=[Depends(allow_super_admin)])
async def get_api_keys(db: AsyncSession = Depends(get_db)):
    """API Keys management mock."""
    return [
        { "id": "1", "name": "Production API", "key": "rp_live_sk_1234567890abcdef", "scope": ["read", "write"], "created_at": "2025-01-01", "last_used": "2025-01-15 14:32" },
        { "id": "2", "name": "Test API", "key": "rp_test_sk_abcdef1234567890", "scope": ["read"], "created_at": "2025-01-05", "last_used": "2025-01-14 09:15" },
    ]

@router.get("/billing", summary="SaaS Billing", dependencies=[Depends(allow_super_admin)])
async def get_billing(db: AsyncSession = Depends(get_db)):
    """Billing and Subscriptions mock."""
    return [
        { "id": "1", "restaurant": "Osh Markazi", "plan": "PRO", "amount": 890000, "status": "active", "next_billing": "2025-02-15" },
        { "id": "2", "restaurant": "Burger House", "plan": "STARTER", "amount": 490000, "status": "active", "next_billing": "2025-02-10" },
        { "id": "3", "restaurant": "Pizza Time", "plan": "ENTERPRISE", "amount": 1490000, "status": "active", "next_billing": "2025-02-20" },
        { "id": "4", "restaurant": "Sushi Bar", "plan": "PRO", "amount": 890000, "status": "pending", "next_billing": "2025-02-05" },
    ]

@router.get("/users", summary="Global foydalanuvchilar", dependencies=[Depends(allow_super_admin)])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """SaaS platformasidagi barcha foydalanuvchilar."""
    from app.models.user import User
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/analytics", summary="Super Admin Analytics", dependencies=[Depends(allow_super_admin)])
async def get_analytics(db: AsyncSession = Depends(get_db)):
    return {
        "total_restaurants": 1247,
        "total_users": 45623,
        "total_orders": 89234,
        "total_revenue": 145200000,
        "growth": 12.5,
    }
