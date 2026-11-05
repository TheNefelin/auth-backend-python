"""Dependency injection module for the Auth Unificado backend.

Provides reusable FastAPI dependencies such as database sessions,
current user retrieval, and rate limiting.
"""

import uuid
from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session, AsyncSessionLocal
from .exceptions import ForbiddenError, UnauthorizedError
from .security import decode_access_token
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
        raise UnauthorizedError("Authentication header missing or invalid")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        # Token inválido/expirado/malformado: es 401, nunca 500.
        raise UnauthorizedError("Invalid or expired token") from None

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid authentication payload")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedError("Invalid user identifier")

    # Fetch user from database
    result = await db.get(User, user_uuid)
    if result is None:
        raise UnauthorizedError("User not found")

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
        raise ForbiddenError("Insufficient privileges")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Solo rol 'admin'."""
    if user.get("role") != "admin":
        raise ForbiddenError("Admin role required")
    return user