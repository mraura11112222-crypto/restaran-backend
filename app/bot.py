"""
Telegram Bot — Verification code generation.
Supports both polling (local dev) and webhook (production/Render).
"""

import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import delete, select

from app.database import engine
from app.config import settings

dp = Dispatcher()
bot: Optional[Bot] = None
table_ready = False


async def ensure_verification_table() -> None:
    global table_ready
    if table_ready:
        return
    table_ready = True


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await ensure_verification_table()

    from app.database import async_session_maker
    async with async_session_maker() as session:
        from app.models.telegram_verification import TelegramVerificationCode

        # Clear expired codes
        await session.execute(
            delete(TelegramVerificationCode).where(
                TelegramVerificationCode.expires_at < datetime.utcnow()
            )
        )

        # Generate unique 5-digit code
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
                # Long expiry so codes don't expire unexpectedly
                expires_at=datetime.utcnow() + timedelta(days=365),
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
    """
    Start the bot.
    - If WEBHOOK_URL env var is set → use webhook mode (production/Render).
    - Otherwise → use polling mode (local development).
    """
    token = os.getenv("BOT_TOKEN") or settings.BOT_TOKEN
    if not token:
        print("[WARN] BOT_TOKEN topilmadi, Telegram bot ishga tushmaydi.")
        return

    global bot
    bot = Bot(token=token)

    webhook_url = os.getenv("WEBHOOK_URL", "").strip()

    if webhook_url:
        # --- WEBHOOK MODE (Render/production) ---
        webhook_path = f"/bot/webhook/{token}"
        full_webhook_url = f"{webhook_url}{webhook_path}"

        await bot.set_webhook(
            url=full_webhook_url,
            drop_pending_updates=True,
        )
        print(f"[OK] Telegram bot webhook set: {full_webhook_url}")
        # Bot will receive updates via the /bot/webhook/<token> route
        # registered in main.py — no blocking polling needed here.
    else:
        # --- POLLING MODE (local dev) ---
        print("[OK] Telegram bot started (polling mode).")
        await dp.start_polling(bot)


async def process_update(update_data: dict) -> None:
    """Process a single update received via webhook."""
    from aiogram.types import Update
    update = Update(**update_data)
    await dp.feed_update(bot, update)
