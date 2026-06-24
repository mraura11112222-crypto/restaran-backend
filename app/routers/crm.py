"""
CRM router — Referral management, Social Media integrations.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.crm import ReferralProgram, SocialMediaIntegration

router = APIRouter()


# --- Schemas ---

class ReferralCreate(BaseModel):
    restaurant_id: uuid.UUID

class ReferralResponse(BaseModel):
    id: uuid.UUID
    referral_code: str
    reward_points: int
    status: str

    class Config:
        from_attributes = True

class SocialMediaConnect(BaseModel):
    platform: str  # INSTAGRAM, TIKTOK, FACEBOOK
    social_account_id: str


# --- Referral Endpoints ---

@router.post("/referral/generate", summary="Tavsiya kodni yaratish", response_model=ReferralResponse)
async def generate_referral_code(
    body: ReferralCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Joriy foydalanuvchi uchun yangi referral kodi yaratadi."""
    import secrets
    code = f"REF-{secrets.token_hex(4).upper()}"

    referral = ReferralProgram(
        referrer_id=current_user.id,
        restaurant_id=body.restaurant_id,
        referral_code=code,
        reward_points=50,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return referral


@router.post("/referral/apply/{code}", summary="Tavsiya kodni ishlatish")
async def apply_referral(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Mijoz tavsiya kodini kiritganda, taklif qilgan odamga ball beradi."""
    result = await db.execute(
        select(ReferralProgram).where(ReferralProgram.referral_code == code)
    )
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral kod topilmadi")
    if referral.referred_user_id:
        raise HTTPException(status_code=400, detail="Bu kod allaqachon ishlatilgan")
    if referral.referrer_id == current_user.id:
        raise HTTPException(status_code=400, detail="O'zingizni taklif qila olmaysiz")

    referral.referred_user_id = current_user.id
    referral.status = "COMPLETED"
    await db.commit()
    return {"detail": "Referral muvaffaqiyatli qo'llanildi", "reward_points": referral.reward_points}


@router.get("/referral/my", summary="Mening tavsiyalarim")
async def my_referrals(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(ReferralProgram).where(ReferralProgram.referrer_id == current_user.id)
    )
    return result.scalars().all()


# --- Social Media Endpoints ---

@router.post("/social/connect", summary="Ijtimoiy tarmoqni ulash")
async def connect_social(
    body: SocialMediaConnect,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Foydalanuvchining ijtimoiy tarmoq akkauntini tizimga bog'laydi."""
    integration = SocialMediaIntegration(
        user_id=current_user.id,
        platform=body.platform.upper(),
        social_account_id=body.social_account_id,
    )
    db.add(integration)
    await db.commit()
    return {"detail": f"{body.platform} muvaffaqiyatli ulandi"}


@router.get("/social/my", summary="Ulangan ijtimoiy tarmoqlar")
async def my_social_accounts(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(SocialMediaIntegration).where(
            SocialMediaIntegration.user_id == current_user.id,
            SocialMediaIntegration.is_active == True,
        )
    )
    return result.scalars().all()
