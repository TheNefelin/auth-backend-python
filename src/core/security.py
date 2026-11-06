"""Security module for the Auth Unificado backend.

Handles JWT token creation/validation, password hashing, and the
authentication/authorization dependencies (get_current_user, require_*).
"""

import hashlib
import json
import base64
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .exceptions import ForbiddenError, InvalidApiKeyError, UnauthorizedError
from .roles import UserRole
from ..models import User, UserRole as UserRoleModel, UserStatus


# Password hashing (pwdlib: recomendado; passlib está sin mantenimiento y
# es incompatible con bcrypt >= 4.1). Se usa bcrypt explícitamente.
pwd_context = PasswordHash((BcryptHasher(),))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    
    to_encode = {"sub": str(subject), "exp": expire, "iat": now}
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


def get_token_from_header(authorization: str | None) -> str | None:
    """Extract bearer token from Authorization header."""
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


def generate_refresh_token() -> str:
    """Genera un refresh token opaco (aleatorio, no predecible)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 del refresh token. La BD guarda solo el hash, nunca el token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --- Autenticación / autorización (dependencias FastAPI) --------------------

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """Resuelve el usuario autenticado desde el JWT (lee el rol real de la BD)."""
    if credentials is None:
        raise UnauthorizedError("Authentication header missing or invalid")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise UnauthorizedError("Invalid or expired token") from None

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid authentication payload")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedError("Invalid user identifier")

    result = await db.get(User, user_uuid)
    if result is None:
        raise UnauthorizedError("User not found")

    role = (
        await db.execute(select(UserRoleModel).where(UserRoleModel.id == result.user_role_id))
    ).scalar_one_or_none()
    user_status = (
        await db.execute(select(UserStatus).where(UserStatus.id == result.status_id))
    ).scalar_one_or_none()

    role_name = role.name if role else UserRole.USER.value
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
    """Cualquier usuario válido (rol 'admin' o 'user')."""
    if user.get("role") not in (UserRole.ADMIN.value, UserRole.USER.value):
        raise ForbiddenError("Insufficient privileges")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Solo rol 'admin'."""
    if user.get("role") != UserRole.ADMIN.value:
        raise ForbiddenError("Admin role required")
    return user


# --- API Key (BFF → API) ----------------------------------------------------

async def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> bool:
    """Verifica la API Key del BFF (header `X-API-Key`).

    Protege el ACCESO A LA RED: solo el BFF debe llamar a la API, nunca el
    navegador directamente. No identifica usuario; eso es `get_current_user`.

    La cabecera se declara OPCIONAL para que el fallo lo decida esta función
    (401 `invalid-api-key`), no la validación de FastAPI (422). Comparación en
    tiempo constante para no filtrar la clave por timing.
    """
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.API_KEY):
        raise InvalidApiKeyError()
    return True