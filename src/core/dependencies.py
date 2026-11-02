"""Dependency injection module for the Auth Unificado backend.

Provides reusable FastAPI dependencies such as database sessions,
current user retrieval, and rate limiting.
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session, AsyncSessionLocal
from .security import get_token_from_header, decode_access_token
from .config import settings


async def get_db() -> Generator[AsyncSession, None, None]:
    """Dependency to get an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = None,
) -> dict:
    """Dependency to get the current authenticated user from JWT token."""
    from .models import User
    
    token = get_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.get(User, user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"id": str(result.id), "email": result.email, "name": result.name}


def get_rate_limit_dependencies(
    requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE,
    requests_per_hour: int = settings.RATE_LIMIT_PER_HOUR,
):
    """Create rate limit dependencies for endpoints."""
    # This is a placeholder - in production would use slowapi or similar
    def rate_limit_check(request: Request) -> bool:
        # Basic rate limiting check
        return True
    
    return rate_limit_check