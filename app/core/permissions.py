"""
Role-based permission system for FastAPI dependencies.

Defines a ``RoleChecker`` callable class that can be injected via
``Depends()`` to gate endpoints by user role.  Pre-built instances
cover common access patterns (admin-only, cashier-level, etc.).

A local ``UserRole`` string enum is defined here to avoid circular
imports with the models package.
"""

from enum import StrEnum
from typing import Any

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

# We use our own oauth2 scheme reference here to avoid importing
# dependencies.py (which would cause a circular import).
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Local UserRole enum (mirrors app.models.enums.UserRole)
# Keep values in sync with the DB / model enum.
# ---------------------------------------------------------------------------

class UserRole(StrEnum):
    """User role values — keep in sync with the DB enum."""

    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
    CASHIER = "CASHIER"
    CHEF = "CHEF"
    BOSS = "BOSS"
    SUPER_ADMIN = "SUPER_ADMIN"


# ---------------------------------------------------------------------------
# RoleChecker dependency
# ---------------------------------------------------------------------------

class RoleChecker:
    """
    FastAPI dependency that authorises a request based on user role.

    Usage (as a route dependency — user is not injected)::

        @router.get("/admin", dependencies=[Depends(allow_admin)])
        async def admin_route(): ...

    Or inject the checked user directly into the handler::

        @router.get("/admin")
        async def admin_route(user=Depends(allow_admin)): ...
    """

    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        token: str = Depends(_oauth2_scheme),
    ) -> Any:
        """
        Resolve the current active user and validate their role.

        We perform a late import of ``get_current_user`` /
        ``get_current_active_user`` inside the method body to break the
        circular import between ``permissions`` ↔ ``dependencies``.
        The OAuth2 token is extracted via the scheme so FastAPI still
        renders the padlock in the OpenAPI docs.
        """
        from app.core.dependencies import get_current_active_user_from_token

        current_user = await get_current_active_user_from_token(token)

        current_role = getattr(current_user.role, "value", current_user.role)
        allowed_roles = [getattr(role, "value", role) for role in self.allowed_roles]

        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user


# ---------------------------------------------------------------------------
# Pre-built permission instances
# ---------------------------------------------------------------------------

allow_admin = RoleChecker([
    UserRole.ADMIN,
    UserRole.BOSS,
    UserRole.SUPER_ADMIN,
])

allow_customer = RoleChecker([
    UserRole.CUSTOMER,
])

allow_cashier = RoleChecker([
    UserRole.CASHIER,
    UserRole.ADMIN,
    UserRole.BOSS,
    UserRole.SUPER_ADMIN,
])

allow_chef = RoleChecker([
    UserRole.CHEF,
    UserRole.ADMIN,
    UserRole.BOSS,
    UserRole.SUPER_ADMIN,
])

allow_boss = RoleChecker([
    UserRole.BOSS,
    UserRole.SUPER_ADMIN,
])

allow_super_admin = RoleChecker([
    UserRole.SUPER_ADMIN,
])

allow_any_authenticated = RoleChecker([
    UserRole.CUSTOMER,
    UserRole.ADMIN,
    UserRole.CASHIER,
    UserRole.CHEF,
    UserRole.BOSS,
    UserRole.SUPER_ADMIN,
])
