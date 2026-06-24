# 🍽️ Restoran Boshqaruv Platformasi — Backend API

**SaaS restoran boshqaruv tizimi** — FastAPI, Neon PostgreSQL, Cloudinary asosida.

## 🚀 Tech Stack

| Texnologiya | Maqsad |
|-------------|--------|
| **FastAPI** | Web framework (async) |
| **Neon PostgreSQL** | Cloud database |
| **SQLAlchemy 2.0** | ORM (async) |
| **Cloudinary** | Rasm/video cloud storage |
| **JWT (python-jose)** | Authentication |
| **Alembic** | Database migrations |
| **Pydantic v2** | Data validation |

## 📋 Rollar

| Rol | Tavsif |
|-----|--------|
| 🛒 **Xaridor** | Menyu ko'rish, buyurtma berish, to'lov, baho |
| 👨‍💼 **Administrator** | Buyurtma qabul, mijozlar, kuryer tayinlash |
| 💰 **Kassir** | To'lov qabul, chek, hisobot, qaytarish |
| 👨‍🍳 **Oshpaz** | Buyurtmalar, holat yangilash, mahsulot |
| 👑 **Boss** | Statistika, xodimlar, menyu, filiallar |

## ⚡ Quick Start

### 1. Virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment variables
```bash
copy .env.example .env
# .env faylini o'z ma'lumotlaringiz bilan to'ldiring
```

### 4. Database migration
```bash
alembic upgrade head
```

### 5. Run server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Settings (.env)
├── database.py          # Neon PostgreSQL connection
├── models/              # SQLAlchemy models (14 models)
├── schemas/             # Pydantic validation schemas
├── routers/             # API endpoints (rollar bo'yicha)
│   ├── auth.py          # 🔐 Register, Login
│   ├── customer.py      # 🛒 Xaridor
│   ├── admin.py         # 👨‍💼 Administrator
│   ├── cashier.py       # 💰 Kassir
│   ├── chef.py          # 👨‍🍳 Oshpaz
│   ├── boss.py          # 👑 Boss
│   ├── menu.py          # 📋 Menyu CRUD
│   └── media.py         # 📸 Rasm/Video upload
├── services/            # Business logic
│   ├── auth_service.py
│   ├── order_service.py
│   ├── payment_service.py
│   ├── media_service.py
│   ├── notification_service.py
│   └── report_service.py
├── core/                # Security, permissions
│   ├── security.py      # JWT, bcrypt
│   ├── permissions.py   # RBAC
│   ├── exceptions.py    # Custom errors
│   └── dependencies.py  # FastAPI deps
└── utils/               # Helpers
```

## 🔑 API Endpoints

### Auth (`/api/v1/auth/`)
- `POST /register` — Restoran ro'yxatdan o'tish
- `POST /login` — Tizimga kirish
- `GET /me` — Joriy foydalanuvchi

### Xaridor (`/api/v1/customer/`)
- `GET /menu` — Menyu ko'rish
- `POST /orders` — Buyurtma berish
- `POST /orders/{id}/pay` — To'lov qilish
- `POST /reviews` — Baho berish

### Administrator (`/api/v1/admin/`)
- `GET /orders` — Buyurtmalar
- `PATCH /orders/{id}/accept` — Qabul qilish
- `POST /orders/{id}/assign-courier` — Kuryer tayinlash

### Kassir (`/api/v1/cashier/`)
- `POST /payments/accept` — To'lov qabul
- `GET /reports/daily` — Kunlik hisobot
- `POST /discounts` — Chegirma

### Oshpaz (`/api/v1/chef/`)
- `GET /orders` — Oshxona buyurtmalari
- `PATCH /orders/{id}/ready` — Tayyor belgisi

### Boss (`/api/v1/boss/`)
- `GET /statistics` — Dashboard
- `GET /finance` — Daromad/Xarajat
- `CRUD /staff` — Xodimlar
- `CRUD /branches` — Filiallar

### Media (`/api/v1/media/`)
- `POST /upload/image` — Rasm yuklash (Cloudinary)
- `POST /upload/video` — Video yuklash (Cloudinary)

## 📄 License

MIT
