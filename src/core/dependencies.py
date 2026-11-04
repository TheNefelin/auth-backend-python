"""Dependency injection module for the Auth Unificado backend.

Provides reusable FastAPI dependencies such as database sessions,
current user retrieval, and rate limiting.
"""

import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session, AsyncSessionLocal
from .security import decode_access_token
from .config import settings
from ..models import User, UserRole, UserStatus


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an async database session.

    La sesión no persiste nada por sí sola: el repository solo hace
    `flush()`. Aquí se hace commit al final de la request (persiste lo
    que flusheó) y rollback si hubo una excepción, para que la request
    sea atómica (p. ej. usuario + identidad se guardan juntos o ninguno).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """Dependency to get the current authenticated user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        # Token inválido/expirado/malformado: es 401, nunca 500.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.get(User, user_uuid)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = (
        await db.execute(select(UserRole).where(UserRole.id == result.user_role_id))
    ).scalar_one_or_none()
    user_status = (
        await db.execute(select(UserStatus).where(UserStatus.id == result.status_id))
    ).scalar_one_or_none()

    role_name = role.name if role else "user"
    status_name = user_status.name if user_status else None

    return {
        "id": str(result.id),
        "email": result.email,
        "name": result.name,
        "role": role_name,
        "status": status_name,
        "is_active": status_name == "activo" if status_name else False,
    }


async def require_user(user: dict = Depends(get_current_user)) -> dict:
    """Cualquier usuario válido (rol 'user' o 'admin')."""
    if user.get("role") not in ("user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Solo rol 'admin'."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


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