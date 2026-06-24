"""
HR router — Staff performance and AI schedule.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_boss
from app.services.ai_service import AIService

router = APIRouter()

@router.post("/schedule/ai-generate", summary="Sun'iy intellekt xodimlari rejalashtiruvchisi", dependencies=[Depends(allow_boss)])
async def generate_schedule(
    target_date: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """AI Staff Scheduler orqali xodimlar uchun maqbul ish jadvalini yaratish."""
    service = AIService(db)
    # Using current user's branch_id if available, else passing empty
    return await service.generate_staff_schedule(
        current_user.restaurant_id, 
        current_user.branch_id or "Barcha filiallar",
        target_date
    )

@router.get("/performance", summary="Xodimlar unumdorligi", dependencies=[Depends(allow_boss)])
async def get_performance(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Xodimlar unumdorligi va KPI baholari."""
    # Mock data
    return [
        {"id": "1", "full_name": "Ali", "role": "Oshpaz", "branch": "Chilonzor", "performance": 98, "hours_this_week": 42},
        {"id": "2", "full_name": "Vali", "role": "Kassir", "branch": "Yunusobod", "performance": 85, "hours_this_week": 36},
    ]
