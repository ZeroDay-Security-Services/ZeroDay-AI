"""Shared FastAPI dependencies: DB session and current-user resolution."""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import TokenError, decode_token
from app.db.base import get_db
from app.db.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedError("Missing bearer token")

    try:
        user_id = decode_token(token, expected_type="access")
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Same resolution as get_current_user, but returns None instead of
    raising when no token is supplied -- for endpoints (like risk scoring)
    that work anonymously but personalize/persist results when logged in."""
    if not token:
        return None
    try:
        user_id = decode_token(token, expected_type="access")
    except TokenError:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user
