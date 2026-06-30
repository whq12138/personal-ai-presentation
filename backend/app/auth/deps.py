"""
Authentication dependencies for FastAPI route injection.
Provides get_current_user, get_optional_user, and tier enforcement.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserTier
from app.services.auth_service import decode_token

security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Value object returned by get_current_user — carries user identity + tier."""

    def __init__(self, user_id: str, email: str, tier: UserTier):
        self.user_id = user_id
        self.email = email
        self.tier = tier

    @property
    def is_premium(self) -> bool:
        return self.tier == UserTier.PREMIUM

    @property
    def allowed_layouts(self) -> list[str]:
        from app.config import get_settings
        s = get_settings()
        if self.tier == UserTier.PREMIUM:
            return s.PREMIUM_LAYOUTS
        return s.FREE_LAYOUTS


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Require valid JWT. Returns CurrentUser. Raises 401 if missing/invalid."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return CurrentUser(
        user_id=user.id,
        email=user.email,
        tier=user.tier,
    )


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[CurrentUser]:
    """Like get_current_user but returns None instead of 401 for unauthenticated requests."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            return None
        return CurrentUser(user_id=user.id, email=user.email, tier=user.tier)
    except HTTPException:
        return None


def require_premium(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that requires a premium-tier user. Raises 402 if free tier."""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="This feature requires a Premium subscription. Upgrade your account.",
        )
    return current_user


def require_layout(layout: str):
    """Factory: returns a dependency that checks if the user's tier allows a layout."""
    async def _check(current_user: CurrentUser = Depends(get_current_user)):
        if layout not in current_user.allowed_layouts:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"The '{layout}' layout is only available on Premium tier. Please upgrade.",
            )
        return current_user
    return _check
