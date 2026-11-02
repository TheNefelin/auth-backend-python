"""Repository module for Auth Unificado backend.

Handles database operations for authentication entities.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import User, UserRole, UserStatus
from ...core.database import get_async_session, AsyncSessionLocal


class UserRepository:
    """Repository for User entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> "User | None":
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> "User | None":
        """Get user by ID."""
        return await self.db.get(User, user_id)

    async def create(self, email: str, password_hash: "str | None", email_verified: bool,
                     name: "str | None", lastname: "str | None") -> "User":
        """Create new user."""
        from sqlalchemy import func

        user = User(
            email=email,
            password_hash=password_hash,
            email_verified=email_verified,
            name=name,
            lastname=lastname,
            created_at=func.now(),
            updated_at=func.now(),
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


class UserStatusRepository:
    """Repository for UserStatus entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> "UserStatus | None":
        """Get status by name."""
        result = await self.db.execute(select(UserStatus).where(UserStatus.name == name))
        return result.scalar_one_or_none()


class AuthProviderRepository:
    """Repository for AuthProvider entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> "AuthProvider | None":
        """Get provider by name."""
        result = await self.db.execute(select(AuthProvider).where(AuthProvider.name == name))
        return result.scalar_one_or_none()

    async def create(self, name: str, display_name: "str | None", is_active: bool) -> "AuthProvider":
        """Create new auth provider."""
        from sqlalchemy import func

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

    async def get_primary_by_user(self, user_id: int) -> "UserIdentity | None":
        """Get primary identity by user."""
        from ...models import UserIdentity as UI

        result = await self.db.execute(
            select(UI).where(UI.user_id == user_id, UI.is_primary == True)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, provider_id: str, provider_user_id: str,
                     provider_user_email: "str | None" = None, is_primary: bool = False) -> "UserIdentity":
        """Create new user identity."""
        from ...models import UserIdentity as UI
        from sqlalchemy import func

        identity = UI(
            user_id=user_id,
            provider_id=provider_id,
            provider_user_id=provider_user_id,
            provider_user_email=provider_user_email,
            is_primary=is_primary,
            is_email_verified=False,
            created_at=func.now(),
        )
        self.db.add(identity)
        await self.db.flush()
        return identity


class UserSessionRepository:
    """Repository for UserSession entity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, refresh_token: str, expires_at) -> "UserSession":
        """Create new session."""
        from ...models import UserSession as US
        from sqlalchemy import func

        session = US(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            is_revoked=False,
            created_at=func.now(),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_refresh_token(self, refresh_token: str) -> "UserSession | None":
        """Get session by refresh token."""
        from ...models import UserSession as US

        result = await self.db.execute(
            select(US).where(US.refresh_token == refresh_token)
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, session: "UserSession") -> "UserSession":
        """Soft delete session (revoke)."""
        session.is_revoked = True
        await self.db.flush()
        return session