"""
AI Features router — recommendations, voice analysis, etc.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.ai_service import AIService

router = APIRouter()

@router.get("/recommendations", summary="AI tavsiyalar")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Mijoz kabineti uchun AI shaxsiy tavsiyalar."""
    service = AIService(db)
    return await service.get_personal_recommendations(current_user.restaurant_id, current_user.id)

@router.post("/voice-order", summary="Ovozli buyurtma tahlili")
async def voice_order(
    audio_text: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Ovozli ma'lumotni tahlil qilib buyurtmaga aylantirish (AI)."""
    service = AIService(db)
    return await service.analyze_voice_order(current_user.restaurant_id, audio_text)
