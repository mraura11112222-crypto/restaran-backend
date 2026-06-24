"""
Auth router — registration, login, token refresh, profile.
"""

import uuid

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import TelegramCodeVerify, Token, UserResponse
from app.schemas.restaurant import RestaurantRegister
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_active_user

router = APIRouter()


from pydantic import BaseModel

class GenericRegister(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    role: str

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Umumiy ro'yxatdan o'tish (Xaridor yoki Xodim)",
)
async def register_generic(
    data: GenericRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Xaridor, Oshpaz, Kassir, Admin va h.k. sifatida ro'yxatdan o'tish.
    Xaridordan boshqa rollar is_active=False bo'lib saqlanadi.
    """
    service = AuthService(db)
    result = await service.register_generic(data)
    return result

@router.post(
    "/register/restaurant",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Restoran ro'yxatdan o'tkazish",
)
async def register_restaurant(
    data: RestaurantRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Yangi restoran va boss foydalanuvchi yaratish.
    - **restaurant_name**: Restoran nomi
    - **admin_phone**: Boss telefon raqami
    - **admin_password**: Parol
    - **admin_full_name**: To'liq ism
    """
    service = AuthService(db)
    result = await service.register_restaurant(data)
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Tizimga kirish",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Telefon raqam va parol bilan tizimga kirish.
    JWT access va refresh tokenlar qaytariladi.
    """
    service = AuthService(db)
    result = await service.login(form_data.username, form_data.password)
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Joriy foydalanuvchi",
)
async def get_current_user_profile(
    current_user=Depends(get_current_active_user),
):
    """Joriy autentifikatsiya qilingan foydalanuvchi ma'lumotlari."""
    return current_user


@router.post(
    "/telegram/verify-code",
    summary="Telegram botdan olingan kodni tekshirish",
)
async def verify_telegram_code(
    data: TelegramCodeVerify,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    verification = await service.verify_telegram_code(data.code)
    return {
        "message": "Kod tasdiqlandi",
        "telegram_id": verification.telegram_id,
        "first_name": verification.first_name,
        "telegram_username": verification.username,
    }

from app.schemas.user import UsernameRegister, UsernameLogin

@router.post(
    "/username/register",
    summary="Username orqali ro'yxatdan o'tish",
)
async def register_username(
    data: UsernameRegister,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.register_username(data)
    return result

@router.post(
    "/username/login",
    summary="Username orqali tizimga kirish",
)
async def login_username(
    data: UsernameLogin,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.login_username(data)
    return result

