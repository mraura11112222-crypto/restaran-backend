import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine
from app.config import settings

dp = Dispatcher()
bot: Optional[Bot] = None
table_ready = False


async def ensure_verification_table() -> None:
    global table_ready
    if table_ready:
        return
    # The table is already created in main.py lifespan, but we can keep this for safety
    table_ready = True


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await ensure_verification_table()
    
    # We create a new session just for this request
    from app.database import async_session_maker
    async with async_session_maker() as session:
        from app.models.telegram_verification import TelegramVerificationCode
        
        # Clear expired codes
        await session.execute(
            delete(TelegramVerificationCode).where(
                TelegramVerificationCode.expires_at < datetime.utcnow()
            )
        )

        code = str(random.randint(10000, 99999))
        existing = await session.execute(
            select(TelegramVerificationCode).where(TelegramVerificationCode.code == code)
        )
        while existing.scalar_one_or_none():
            code = str(random.randint(10000, 99999))
            existing = await session.execute(
                select(TelegramVerificationCode).where(TelegramVerificationCode.code == code)
            )

        import uuid
        session.add(
            TelegramVerificationCode(
                id=uuid.uuid4(),
                code=code,
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                expires_at=datetime.utcnow() + timedelta(days=3650),
            )
        )
        await session.commit()

    response_text = (
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"RestoPro tizimiga ro'yxatdan o'tish uchun kodingiz:\n\n"
        f"🔐 <b>{code}</b>\n\n"
        f"<i>Ushbu kodni saytdagi maxsus oynaga kiriting.</i>"
    )

    await message.answer(response_text, parse_mode="HTML")


async def start_bot() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("[WARN] BOT_TOKEN topilmadi, Telegram bot ishga tushmaydi.")
        return
        
    global bot
    bot = Bot(token=token)
    print("[OK] Telegram bot started.")
    await dp.start_polling(bot)
