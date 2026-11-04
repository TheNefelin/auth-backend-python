"""Service module for Auth Unificado backend.

Contains business logic for authentication operations.
"""

import uuid

from ...core.dependencies import get_db
from ...core.security import create_access_token, verify_password
from ...core.exceptions import CredentialsException
from ...schemas.dtos import UserLogin, UserRegister, UserProfile, Token, UserProfile
from ...models import User
from .repository import UserRepository, UserRoleRepository, UserStatusRepository, \
    AuthProviderRepository, UserIdentityRepository, UserSessionRepository
from datetime import datetime


class AuthService:
    """Service class for authentication business logic."""

    def __init__(self, db_session=None):
        self.db = db_session

    async def login(self, credentials: UserLogin) -> dict:
        """Authenticate user with email and password."""
        repo = UserRepository(self.db)
        user = await repo.get_by_email(credentials.email)

        if not user or not user.can_authenticate():
            raise CredentialsException()

        if not verify_password(credentials.password, user.password_hash):  # type: ignore
            raise CredentialsException()

        if not user.is_active:  # type: ignore
            raise CredentialsException("Account is disabled")

        access_token = create_access_token(subject=str(user.id))

        return {
            "access_token": access_token,
            "expires_in": 900,
            "token_type": "bearer",
        }

    async def google_login(self, google_token: str) -> dict:
        from sqlalchemy import select

        from ...models import User, UserIdentity
        from .google_service import fetch_google_userinfo, verify_google_token
        from .repository import AuthProviderRepository

        info = await verify_google_token(google_token)
        if not info:
            raise CredentialsException("Invalid Google token")

        # Datos del perfil (nombre/imagen): source de verdad = userinfo; degradación suave si falla.
        profile = await fetch_google_userinfo(google_token) or {}
        given_name = profile.get("given_name") or info.get("given_name")
        family_name = profile.get("family_name") or info.get("family_name")
        picture = profile.get("picture")

        provider = await AuthProviderRepository(self.db).get_by_name("google")
        if provider is None:
            raise RuntimeError("Seed faltante: no existe el auth_provider 'google'")
        if not provider.is_active:
            raise CredentialsException("Google login is disabled")

        # Find existing identity by (provider, provider_user_id)
        result = await self.db.execute(
            select(UserIdentity).where(
                UserIdentity.provider_id == provider.id,
                UserIdentity.provider_user_id == info["sub"],
            )
        )
        identity = result.scalar_one_or_none()

        if identity is not None:
            user = await self.db.get(User, identity.user_id)
            if user is not None:
                # Refrescar perfil en cada login (la URL de la foto cambia si el usuario la cambia).
                user.email = info.get("email") or user.email
                user.name = given_name or user.name
                user.lastname = family_name or user.lastname
                user.picture_url = picture or user.picture_url
                user.email_verified = str(info.get("email_verified", user.email_verified)).lower() == "true"
                await self.db.flush()
        else:
            # Create user + identity
            repo = UserRepository(self.db)
            user = await repo.create(
                email=info.get("email"),
                password_hash=None,
                email_verified=True,
                name=given_name,
                lastname=family_name,
                picture_url=picture,
            )
            id_repo = UserIdentityRepository(self.db)
            await id_repo.create(
                user_id=user.id,
                provider_id=provider.id,
                provider_user_id=info["sub"],
                email=info.get("email"),
                is_primary=True,
            )

        if user is None or not user.can_authenticate():
            raise CredentialsException("Account disabled")

        access_token = create_access_token(subject=str(user.id))
        return {"access_token": access_token, "token_type": "bearer", "expires_in": 900}

    async def register(self, user_data: UserRegister) -> dict:
        """Register new user."""
        repo = UserRepository(self.db)

        # Check if user already exists
        existing = await repo.get_by_email(user_data.email)
        if existing:
            raise CredentialsException("Email already registered")

        # Create user
        user = await repo.create(
            email=user_data.email,
            password_hash=None,  # Will be set after verification
            email_verified=False,
            name=user_data.name,
            lastname=user_data.lastname,
        )

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "lastname": user.lastname,
            "registered": True,
        }

    async def get_profile(self, user_id: str) -> UserProfile:
        """Get user profile."""
        repo = UserRepository(self.db)
        user = await repo.get_by_id(uuid.UUID(user_id))

        if not user:
            raise CredentialsException("User not found")

        role = await UserRoleRepository(self.db).get_by_id(user.user_role_id)
        status = await UserStatusRepository(self.db).get_by_id(user.status_id)
        identity = await UserIdentityRepository(self.db).get_primary_by_user(user.id)
        provider = await AuthProviderRepository(self.db).get_by_id(identity.provider_id) if identity else None

        return UserProfile(
            id=str(user.id),
            email=user.email,
            name=user.name,
            lastname=user.lastname,
            picture_url=user.picture_url,
            email_verified=user.email_verified,
            is_active=(status.name == "activo") if status else False,
            role=role.name if role else None,
            status=status.name if status else None,
            provider=provider.name if provider else None,
        )

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh JWT token."""
        from ...models import UserSession

        repo = UserSessionRepository(self.db)
        session = await repo.get_by_refresh_token(refresh_token)

        if not session or session.is_revoked:
            raise CredentialsException("Invalid or revoked refresh token")

        if session.expires_at < datetime.utcnow():  # type: ignore
            await repo.soft_delete(session)
            raise CredentialsException("Refresh token has expired")

        from ...models import User as UserModel
        user = await self.db.get(UserModel, session.user_id)  # type: ignore

        if not user or not user.is_active:
            raise CredentialsException("User not found or disabled")

        # Revoke old token and create new ones
        await repo.soft_delete(session)

        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = await repo.create(
            user_id=user.id,
            refresh_token="",  # Will be set by the caller
            expires_at=None,  # Will be set by the caller
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": 900,
            "token_type": "bearer",
        }

    async def logout(self, user_id: str) -> dict:
        """Logout user."""
        repo = UserSessionRepository(self.db)

        # Revoke all active sessions for user
        # In a real implementation, we'd find and revoke the specific session
        return {"status": "logged_out"}
