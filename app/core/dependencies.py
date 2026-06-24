"""
FastAPI dependencies for authentication and request-scoped resources.

Provides:
- ``get_current_user``         — extract & validate user from JWT Bearer token
- ``get_current_active_user``  — ensure user is active
- ``get_current_restaurant``   — load the restaurant tied to the current user
"""

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings  # noqa: F401 — used indirectly via security
from app.core.security import decode_token
from app.database import async_session, get_db

# ---------------------------------------------------------------------------
# OAuth2 scheme — points to the login endpoint
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Decode the JWT access token and load the corresponding user from the DB.

    Raises 401 if:
    - the token is expired or malformed
    - the ``sub`` claim is missing
    - no user with that id exists in the database
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    token_type: str | None = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Late import to avoid circular dependency (models ↔ core)
    from app.models.user import User  # noqa: WPS433

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user_from_token(token: str):
    """
    Resolve an active user from a bearer token when a dependency already
    extracted the token string.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    from app.models.user import User  # noqa: WPS433

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


# ---------------------------------------------------------------------------
# get_current_active_user
# ---------------------------------------------------------------------------

async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """
    Ensure the authenticated user's account is active.

    Raises 403 if ``is_active`` is False (account disabled / banned).
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


# ---------------------------------------------------------------------------
# get_current_restaurant
# ---------------------------------------------------------------------------

async def get_current_restaurant(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Load the restaurant associated with the current user.

    Reads ``restaurant_id`` from the user model and fetches the
    corresponding ``Restaurant`` row.  Returns ``None`` if the user
    has no restaurant (e.g. a CUSTOMER or SUPER_ADMIN).
    """
    restaurant_id = getattr(current_user, "restaurant_id", None)
    if restaurant_id is None:
        return None

    # Late import to avoid circular dependency
    from app.models.restaurant import Restaurant  # noqa: WPS433

    result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    return restaurant
