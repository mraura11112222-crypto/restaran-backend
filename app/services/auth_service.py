"""
Authentication service — registration, login, token management.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import BadRequestException, UnauthorizedException, ConflictException, NotFoundException


class AuthService:
    """Handles user authentication and registration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_generic(self, data) -> dict:
        """Register a generic user (Customer or Staff). Assigns to first restaurant."""
        from app.models.user import User, UserRole
        from app.models.restaurant import Restaurant
        
        # Get default restaurant
        res = await self.db.execute(select(Restaurant).limit(1))
        restaurant = res.scalar_one_or_none()
        
        if not restaurant:
            # Create a dummy restaurant if none exists
            restaurant = Restaurant(
                id=uuid.uuid4(),
                name="RestoPro Default",
                phone="+998000000000",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(restaurant)
            await self.db.flush()

        # Check if phone already used
        phone_to_use = data.phone or data.email
        existing = await self.db.execute(
            select(User).where(User.phone == phone_to_use)
        )
        if existing.scalars().first():
            raise ConflictException("Bu telefon yoki email raqam allaqachon ro'yxatdan o'tgan")

        role_enum = UserRole.CUSTOMER
        try:
            role_enum = UserRole[data.role.upper()]
        except KeyError:
            pass

        is_active = (role_enum == UserRole.CUSTOMER)

        user = User(
            id=uuid.uuid4(),
            restaurant_id=restaurant.id,
            phone=phone_to_use,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            role=role_enum,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(user)
        await self.db.flush()
        
        if is_active:
            token_data = {
                "sub": str(user.id),
                "role": user.role.value,
                "restaurant_id": str(restaurant.id),
            }
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user,
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz"
            }
        else:
            return {
                "message": "Hisobingiz yaratildi, admin tasdiqlashini kuting",
                "requires_approval": True,
                "user": user
            }

    async def register_restaurant(self, data) -> dict:
        """
        Register a new restaurant with an admin user.
        Creates restaurant + first admin user in one transaction.
        """
        from app.models.restaurant import Restaurant
        from app.models.user import User, UserRole

        # Check if phone already used
        existing = await self.db.execute(
            select(User).where(User.phone == data.admin_phone)
        )
        if existing.scalars().first():
            raise ConflictException("Bu telefon raqam allaqachon ro'yxatdan o'tgan")

        # Create restaurant
        restaurant = Restaurant(
            id=uuid.uuid4(),
            name=data.restaurant_name,
            phone=data.admin_phone,
            address=getattr(data, "address", ""),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(restaurant)
        await self.db.flush()

        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            restaurant_id=restaurant.id,
            phone=data.admin_phone,
            password_hash=get_password_hash(data.admin_password),
            full_name=data.admin_full_name,
            role=UserRole.BOSS,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(admin_user)
        await self.db.flush()

        # Generate tokens
        token_data = {
            "sub": str(admin_user.id),
            "role": admin_user.role.value,
            "restaurant_id": str(restaurant.id),
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": admin_user,
            "restaurant": restaurant,
        }

    async def login(self, phone: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        from app.models.user import User

        result = await self.db.execute(
            select(User).where(User.phone == phone, User.is_active == True)
        )
        user = result.scalars().first()

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Telefon raqam yoki parol noto'g'ri")

        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "restaurant_id": str(user.restaurant_id),
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def create_staff(self, data, restaurant_id: uuid.UUID) -> "User":
        """Create a new staff member (admin, cashier, chef, etc.)."""
        from app.models.user import User

        # Check phone uniqueness within restaurant
        existing = await self.db.execute(
            select(User).where(
                User.phone == data.phone,
                User.restaurant_id == restaurant_id,
            )
        )
        if existing.scalars().first():
            raise ConflictException("Bu telefon raqam allaqachon mavjud")

        user = User(
            id=uuid.uuid4(),
            restaurant_id=restaurant_id,
            branch_id=getattr(data, "branch_id", None),
            phone=data.phone,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> "User":
        """Get user by ID."""
        from app.models.user import User

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Foydalanuvchi topilmadi")
        return user

    async def register_username(self, data) -> dict:
        """Register a new user using username."""
        from app.models.user import User, UserRole
        from app.models.restaurant import Restaurant

        telegram_code = await self.verify_telegram_code(data.telegram_code)

        # Check if username already used
        existing = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        if existing.scalars().first():
            raise ConflictException("Bu username allaqachon band")

        existing_telegram = await self.db.execute(
            select(User).where(User.telegram_id == telegram_code.telegram_id)
        )
        if existing_telegram.scalars().first():
            raise ConflictException("Bu Telegram akkaunt allaqachon ro'yxatdan o'tgan")

        # Get default restaurant
        res = await self.db.execute(select(Restaurant).limit(1))
        restaurant = res.scalar_one_or_none()
        
        if not restaurant:
            restaurant = Restaurant(
                id=uuid.uuid4(),
                name="RestoPro Default",
                phone="+998000000000",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(restaurant)
            await self.db.flush()

        role_enum = UserRole.CUSTOMER
        try:
            role_enum = UserRole[data.role.upper()]
        except KeyError:
            pass

        # If role is NOT customer, they need admin approval
        is_active = (role_enum == UserRole.CUSTOMER)

        user = User(
            id=uuid.uuid4(),
            restaurant_id=restaurant.id,
            telegram_id=telegram_code.telegram_id,
            username=data.username,
            full_name=data.full_name,
            password_hash=get_password_hash(data.password),
            role=role_enum,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(user)
        telegram_code.used = True
        await self.db.flush()
        
        if is_active:
            token_data = {
                "sub": str(user.id),
                "role": user.role.value,
                "restaurant_id": str(restaurant.id),
            }
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user,
                "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz"
            }
        else:
            return {
                "requires_approval": True,
                "message": "Hisobingiz yaratildi. Admin tasdiqlashini kuting.",
                "user": user
            }

    async def login_username(self, data) -> dict:
        """Login using username and password."""
        from app.models.user import User

        result = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Username yoki parol noto'g'ri")

        if not user.is_active:
            raise UnauthorizedException("Kutilmoqda. Admin tasdiqlashi kerak.")

        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "restaurant_id": str(user.restaurant_id),
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    async def verify_telegram_code(self, code: str):
        """Validate a Telegram bot code without consuming it."""
        from app.models.telegram_verification import TelegramVerificationCode

        result = await self.db.execute(
            select(TelegramVerificationCode).where(
                TelegramVerificationCode.code == code.strip(),
                TelegramVerificationCode.used == False,
            )
        )
        verification = result.scalar_one_or_none()

        if not verification:
            raise BadRequestException("Telegram kodi noto'g'ri yoki allaqachon ishlatilgan")

        # if verification.expires_at < datetime.utcnow():
        #     raise BadRequestException("Telegram kodi muddati tugagan. Botdan yangi kod oling")

        return verification


