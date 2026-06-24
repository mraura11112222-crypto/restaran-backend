"""
Demo ma'lumotlarni tozalash scripti
Faqat demo hisoblar saqlanib, barcha test ma'lumotlari o'chiriladi
"""
import asyncio
import sys
from sqlalchemy import text
from app.database import engine

# Saqlanadigan demo hisoblar
DEMO_ACCOUNTS = [
    "admin@restopro.com",
    "boss@restopro.com", 
    "chef@restopro.com",
    "cashier@restopro.com",
    "customer@restopro.com",
]

# O'chirish tartibi (foreign key bog'liqliklari inobatga olingan)
TABLES_TO_CLEAR = [
    # Order related
    "order_items",
    "orders",
    "payments",
    "deliveries",
    
    # Customer related
    "reviews",
    "notifications",
    "wishlists",
    "referrals",
    "loyalty_transactions",
    "bonus_cards",
    
    # Admin related
    "promo_codes",
    "support_tickets",
    
    # Inventory related
    "inventory_transactions",
    "inventory_items",
    "suppliers",
    
    # HR related
    "payrolls",
    "staff_performance",
    "work_schedules",
    "recruitment_candidates",
    "staff_trainings",
    "skill_matrices",
    
    # Analytics & AI
    "market_trends",
    "competitor_data",
    "customer_segments",
    "investor_reports",
    
    # Fleet
    "delivery_routes",
    "delivery_fleet",
    
    # IoT
    "kitchen_iot_devices",
    
    # Media (Cloudinary dagi rasmlar saqlanib, faqat DB yozuvlari o'chiriladi)
    "media",
    
    # Settings
    "integration_configs",
    "social_media_integrations",
    "financial_integrations",
    "tax_rules",
    "currencies",
    "global_tenant_settings",
    
    # Tables & QR
    "table_sessions",
    "qr_codes",
]

async def clear_demo_data():
    """Barcha demo ma'lumotlarni o'chirish"""
    print("=" * 60)
    print("🧹 Demo ma'lumotlarni tozalash...")
    print("=" * 60)
    
    async with engine.begin() as conn:
        # Foreign key cheklovlarini vaqtincha o'chirish
        await conn.execute(text("SET session_replication_role = replica;"))
        
        for table in TABLES_TO_CLEAR:
            try:
                result = await conn.execute(text(f"DELETE FROM {table}"))
                count = result.rowcount
                print(f"✅ {table}: {count} ta yozuv o'chirildi")
            except Exception as e:
                print(f"⚠️  {table}: Xatolik - {e}")
        
        # Foreign key cheklovlarini tiklash
        await conn.execute(text("SET session_replication_role = DEFAULT;"))
        
        print("\n" + "=" * 60)
        print("👥 Demo hisoblar saqlab qolindi:")
        for email in DEMO_ACCOUNTS:
            print(f"   - {email}")
        print("=" * 60)
        
        # Qolgan ma'lumotlar sonini tekshirish
        print("\n📊 Qolgan ma'lumotlar:")
        
        tables_to_check = [
            "users",
            "restaurants", 
            "branches",
            "categories",
            "menu_items",
            "recipes",
            "recipe_ingredients",
        ]
        
        for table in tables_to_check:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   - {table}: {count} ta")
            except Exception as e:
                print(f"   - {table}: Xatolik - {e}")

if __name__ == "__main__":
    print("\n⚠️  DIQQAT! Bu script barcha demo ma'lumotlarni o'chiradi!")
    print("Faqat demo hisoblar saqlanib qoladi.\n")
    print("Auto-confirm: yes\n")
    
    asyncio.run(clear_demo_data())
    print("\n✅ Tozalash tugallandi!")
