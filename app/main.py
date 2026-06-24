"""
Restoran Management Platform - FastAPI Entry Point
====================================================
SaaS platformasi: Xaridor, Administrator, Kassir, Oshpaz, Boss rollari
Tech Stack: FastAPI + Neon PostgreSQL + Cloudinary
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    if settings.DEBUG:
        try:
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config("alembic.ini")
            await asyncio.wait_for(
                asyncio.to_thread(command.upgrade, alembic_cfg, "head"),
                timeout=15,
            )
            print("[OK] Alembic migrations applied successfully.")

            from sqlalchemy import text
            from app.database import engine
            async with engine.begin() as conn:
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512);"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS branch_id UUID;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT;"))
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255);"))
                await conn.execute(text("ALTER TABLE users ALTER COLUMN phone DROP NOT NULL;"))
                await conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;"))
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS telegram_verification_codes (
                        id UUID PRIMARY KEY,
                        code VARCHAR(10) NOT NULL UNIQUE,
                        telegram_id BIGINT NOT NULL,
                        first_name VARCHAR(255),
                        username VARCHAR(255),
                        expires_at TIMESTAMP NOT NULL,
                        used BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_verification_codes_code ON telegram_verification_codes (code);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_verification_codes_telegram_id ON telegram_verification_codes (telegram_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_telegram_verification_codes_expires_at ON telegram_verification_codes (expires_at);"))
                try:
                    await conn.execute(text("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPER_ADMIN';"))
                except Exception:
                    pass
            print("[OK] Manual DB fixes applied successfully.")
        except Exception as e:
            print(f"[WARN] Alembic migrations / DB fixes failed: {e}")
    else:
        print("[OK] Startup migrations skipped because DEBUG is false.")

    # Start Telegram Bot in background
    bot_task = None
    try:
        from app.bot import start_bot
        bot_task = asyncio.create_task(start_bot())
    except Exception as e:
        print(f"[WARN] Failed to start Telegram Bot: {e}")

    if settings.DEBUG:
        try:
            await init_db()
            print("[OK] Database connected successfully")
        except Exception as e:
            print(f"[WARN] Database connection failed: {e}")
            print("   Server will start without database. Set DATABASE_URL in .env")
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "🍽️ Restoran Boshqaruv Platformasi — SaaS backend.\n\n"
        "**Rollar:** Xaridor, Administrator, Kassir, Oshpaz, Boss\n\n"
        "**Texnologiyalar:** FastAPI + Neon PostgreSQL + Cloudinary"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    error_msg = errors[0]["msg"] if errors else "Ma'lumotlar xato kiritildi"
    # Provide a simple string so the frontend doesn't crash on React Error #31
    return JSONResponse(
        status_code=422,
        content={"detail": f"Xatolik: {error_msg}"},
    )

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Include Routers ---
from app.routers import (  # noqa: E402
    auth,
    customer,
    admin,
    cashier,
    chef,
    boss,
    menu,
    media,
    super_admin,
    ai_features,
    inventory,
    analytics,
    hr,
    crm,
    finance,
    fleet,
    hr_extended,
    support,
    tables,
    reviews,
    loyalty,
    wallet,
)

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["🔐 Authentication"])
app.include_router(customer.router, prefix=f"{API_PREFIX}/customer", tags=["🛒 Xaridor"])
app.include_router(wallet.router, prefix=f"{API_PREFIX}/wallet", tags=["💳 Hamyon"])
app.include_router(admin.router, prefix=f"{API_PREFIX}/admin", tags=["👨‍💼 Administrator"])
app.include_router(cashier.router, prefix=f"{API_PREFIX}/cashier", tags=["💰 Kassir"])
app.include_router(chef.router, prefix=f"{API_PREFIX}/chef", tags=["👨‍🍳 Oshpaz"])
app.include_router(boss.router, prefix=f"{API_PREFIX}/boss", tags=["👑 Boss"])
app.include_router(menu.router, prefix=f"{API_PREFIX}/menu", tags=["📋 Menyu"])
app.include_router(media.router, prefix=f"{API_PREFIX}/media", tags=["📸 Media"])

# Yangi modullar:
app.include_router(super_admin.router, prefix=f"{API_PREFIX}/super-admin", tags=["🛡️ Super Admin"])
app.include_router(inventory.router, prefix=f"{API_PREFIX}/inventory", tags=["📦 Inventar"])
app.include_router(analytics.router, prefix=f"{API_PREFIX}/analytics", tags=["📊 Analitika"])
# AI Features disabled - uncomment when needed
# app.include_router(ai_features.router, prefix=f"{API_PREFIX}/ai", tags=["🤖 AI & Mijoz tajribasi"])
app.include_router(hr.router, prefix=f"{API_PREFIX}/hr", tags=["👥 Xodimlar (HR)"])

# v2.0 — Global SaaS Engines:
app.include_router(crm.router, prefix=f"{API_PREFIX}/crm", tags=["🤝 CRM & Referral"])
app.include_router(finance.router, prefix=f"{API_PREFIX}/finance", tags=["💰 Moliya & Soliq"])
app.include_router(fleet.router, prefix=f"{API_PREFIX}/fleet", tags=["🚚 Avtopark & Dronlar"])
app.include_router(hr_extended.router, prefix=f"{API_PREFIX}/hr-extended", tags=["🎓 HR Kengaytirilgan"])
app.include_router(support.router, prefix=f"{API_PREFIX}/support", tags=["🎧 Qo'llab-quvvatlash"])
app.include_router(tables.router, prefix=f"{API_PREFIX}/tables", tags=["🪑 Stollar & QR"])

# v2.1 — Customer Experience:
app.include_router(reviews.router, prefix=f"{API_PREFIX}/reviews", tags=["⭐ Sharhlar & Reyting"])
app.include_router(loyalty.router, prefix=f"{API_PREFIX}/loyalty", tags=["🎁 Sodiqlik & Bonus"])


# --- Root Endpoint ---
@app.get("/", tags=["🏠 Root"])
async def root():
    """API root - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["🏠 Root"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# --- Telegram Bot Webhook ---
@app.post("/bot/webhook/{token}", include_in_schema=False)
async def telegram_webhook(token: str, request: Request):
    """
    Telegram webhook endpoint.
    Telegram sends updates here when WEBHOOK_URL is configured.
    """
    import os
    bot_token = os.getenv("BOT_TOKEN") or settings.BOT_TOKEN
    if token != bot_token:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    try:
        from app.bot import process_update
        update_data = await request.json()
        await process_update(update_data)
    except Exception as e:
        print(f"[WARN] Webhook processing error: {e}")
    return {"ok": True}

# --- WebSockets ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real app, you'd route this specific to user/roles
            await manager.broadcast(f"Server update for {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
