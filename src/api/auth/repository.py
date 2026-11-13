"""Repository module for Auth Unificado backend.

Handles database operations for authentication entities.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import hash_refresh_token
from ...models import AuthProvider, User, UserIdentity, UserRole, UserSession, UserStatus


class UserRepository:
    """Repository for User entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> "User | None":
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> "User | None":
        """Get user by ID."""
        return await self.db.get(User, user_id)

    async def create(self, email: str, password_hash: "str | None", email_verified: bool,
                     name: "str | None", lastname: "str | None", picture_url: "str | None" = None) -> "User":
        """Create new user con rol y status por defecto del seed (user / activo)."""
        role = (await self.db.execute(select(UserRole).where(UserRole.name == "user"))).scalar_one_or_none()
        if role is None:
            raise RuntimeError("Seed faltante: no existe el rol 'user' (user_roles)")
        status = (await self.db.execute(select(UserStatus).where(UserStatus.name == "activo"))).scalar_one_or_none()
        if status is None:
            raise RuntimeError("Seed faltante: no existe el status 'activo' (user_status)")

        user = User(
            email=email,
            password_hash=password_hash,
            email_verified=email_verified,
            name=name,
            lastname=lastname,
            picture_url=picture_url,
            user_role_id=role.id,
            status_id=status.id,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update(self, user: "User", **kwargs) -> "User":
        """Update user fields."""
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self.db.flush()
        return user

    async def soft_delete(self, user: "User") -> "User":
        """Soft delete user (set deleted_at)."""
        user.deleted_at = func.now()
        await self.db.flush()
        return user


class UserRoleRepository:
    """Repository for UserRole entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> "UserRole | None":
        """Get role by name."""
        result = await self.db.execute(select(UserRole).where(UserRole.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, role_id: int) -> "UserRole | None":
        """Get role by ID."""
        return await self.db.get(UserRole, role_id)


class UserStatusRepository:
    """Repository for UserStatus entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> "UserStatus | None":
        """Get status by name."""
        result = await self.db.execute(select(UserStatus).where(UserStatus.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, status_id: int) -> "UserStatus | None":
        """Get status by ID."""
        return await self.db.get(UserStatus, status_id)


class AuthProviderRepository:
    """Repository for AuthProvider entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> "AuthProvider | None":
        """Get provider by name."""
        result = await self.db.execute(select(AuthProvider).where(AuthProvider.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, provider_id: int) -> "AuthProvider | None":
        """Get provider by ID."""
        return await self.db.get(AuthProvider, provider_id)

    async def create(self, name: str, display_name: "str | None", is_active: bool) -> "AuthProvider":
        """Create new auth provider."""
        provider = AuthProvider(
            name=name,
            display_name=display_name,
            is_active=is_active,
            created_at=func.now(),
        )
        self.db.add(provider)
        await self.db.flush()
        return provider


class UserIdentityRepository:
    """Repository for UserIdentity entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_primary_by_user(self, user_id: uuid.UUID) -> "UserIdentity | None":
        """Get primary identity by user."""
        result = await self.db.execute(
            select(UserIdentity).where(UserIdentity.user_id == user_id, UserIdentity.is_primary == True)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, provider_id: int, provider_user_id: str,
                     email: "str | None" = None, is_primary: bool = False,
                     profile_data: "dict | None" = None) -> "UserIdentity":
        """Create new user identity (provider_id es el id de auth_providers)."""
        identity = UserIdentity(
            user_id=user_id,
            provider_id=provider_id,
            provider_user_id=provider_user_id,
            email=email,
            is_primary=is_primary,
            profile_data=profile_data,
        )
        self.db.add(identity)
        await self.db.flush()
        return identity


class UserSessionRepository:
    """Repository for UserSession entity.

    El refresh_token se recibe en CLARO desde el service y aquí se hashea
    antes de tocar la BD: nunca se persiste el token en claro.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID, refresh_token: str, expires_at) -> "UserSession":
        """Create new session (guarda el hash del refresh token)."""
        session = UserSession(
            user_id=user_id,
            refresh_token=hash_refresh_token(refresh_token),
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_refresh_token(self, refresh_token: str) -> "UserSession | None":
        """Get session by refresh token (busca por hash)."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.refresh_token == hash_refresh_token(refresh_token))
        )
        return result.scalar_one_or_none()

    async def touch(self, session: "UserSession") -> None:
        """Actualiza last_used_at (sesión activa)."""
        session.last_used_at = func.now()
        await self.db.flush()

    async def revoke(self, session: "UserSession") -> None:
        """Revoca la sesión."""
        session.is_revoked = True
        await self.db.flush()

    async def revoke_if_active(self, session_id: uuid.UUID) -> bool:
        """Revoca la sesión solo si seguía activa (revocación atómica).

        Devuelve True si afectó una fila (la revocó), False si ya estaba
        revocada (otra petición la usó antes → posible reuso).
        """
        result = await self.db.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        await self.db.flush()
        return result.rowcount == 1

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoca todas las sesiones activas del usuario (logout global)."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.user_id == user_id, UserSession.is_revoked == False)  # noqa: E712
        )
        for session in result.scalars().all():
            session.is_revoked = True
        await self.db.flush()

    async def soft_delete(self, session: "UserSession") -> "UserSession":
        """Soft delete session (revoke)."""
        session.is_revoked = True
        await self.db.flush()
        return session