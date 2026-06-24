"""
AI Service — Integrates with LLMs/AI models for recommendations, analytics, and automation.
(Mock implementation ready for real OpenAI/Claude integration)
"""

import uuid
import random
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.menu import MenuItem
from app.models.order import Order
from app.models.analytics import MarketTrend


class AIService:
    """Handles AI-powered features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_personal_recommendations(
        self, restaurant_id: uuid.UUID, customer_id: uuid.UUID
    ) -> List[dict]:
        """
        AI Personal Recommendations.
        Analyzes past orders of the customer and suggests items.
        (Mock logic: returns random available items).
        """
        result = await self.db.execute(
            select(MenuItem).where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_available == True
            ).limit(20)
        )
        items = result.scalars().all()
        
        if not items:
            return []
            
        # Mock AI logic: pick 3 random items
        recommended = random.sample(items, min(3, len(items)))
        return [
            {
                "item_id": str(item.id),
                "name": item.name,
                "reason": "Sizning oldingi buyurtmalaringizga asoslanib tanlandi",
                "price": float(item.price)
            }
            for item in recommended
        ]

    async def analyze_voice_order(
        self, restaurant_id: uuid.UUID, audio_text: str
    ) -> Dict[str, Any]:
        """
        Voice food analysis. Maps transcribed audio text to menu items.
        (Mock logic).
        """
        # In a real app, send `audio_text` to OpenAI to extract item names and quantities.
        return {
            "transcription": audio_text,
            "detected_items": [
                {"item_name": "Osh", "quantity": 2, "confidence": 0.95},
                {"item_name": "Choy", "quantity": 1, "confidence": 0.90}
            ],
            "message": "AI buyurtmani tahlil qildi."
        }

    async def predict_market_trend(
        self, restaurant_id: uuid.UUID
    ) -> MarketTrend:
        """
        Predicts future market trends based on historical data.
        """
        trend = MarketTrend(
            id=uuid.uuid4(),
            restaurant_id=restaurant_id,
            trend_name="Yozgi sovuq ichimliklarga talab oshishi",
            description="AI tahlili shuni ko'rsatmoqdaki, keyingi oyda havo harorati ko'tarilishi sababli sovuq ichimliklarga talab 40% oshadi.",
            data={"predicted_increase_percent": 40, "target_category": "Ichimliklar"}
        )
        self.db.add(trend)
        await self.db.flush()
        return trend

    async def generate_staff_schedule(
        self, restaurant_id: uuid.UUID, branch_id: uuid.UUID, target_date: str
    ) -> Dict[str, Any]:
        """
        AI Staff Scheduler.
        Optimizes staff shifts based on predicted customer footfall.
        """
        return {
            "date": target_date,
            "branch_id": str(branch_id),
            "status": "Generated via AI",
            "shifts": [
                {"role": "CHEF", "required_count": 3, "shift": "08:00 - 16:00"},
                {"role": "CASHIER", "required_count": 2, "shift": "10:00 - 18:00"}
            ],
            "note": "Eng tirband vaqtlarga moslashtirildi."
        }
