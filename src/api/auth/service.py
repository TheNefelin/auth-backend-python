"""Service module for Auth Unificado backend.

Contains business logic for authentication operations.
"""

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

    async def google_login(self, id_token: str) -> dict:
        import httpx
        from .google_service import verify_google_token
        info = await verify_google_token(id_token)
        if not info or not info.get("email_verified"):
            raise CredentialsException("Invalid Google token")

        # Find existing identity
        from ...models import UserIdentity as UI
        result = await self.db.execute(
            __import__("sqlalchemy").select(UI).where(UI.provider_id == "google", UI.provider_user_id == info["sub"])
        )
        identity = result.scalar_one_or_none()

        if identity:
            user = await self.db.get(__import__("...models", fromlist=["User"]).User, identity.user_id)
        else:
            # Create user + identity
            repo = UserRepository(self.db)
            user = await repo.create(
                email=info.get("email"),
                password_hash=None,
                email_verified=True,
                name=info.get("given_name"),
                lastname=info.get("family_name"),
            )
            id_repo = UserIdentityRepository(self.db)
            await id_repo.create(
                user_id=user.id,
                provider_id="google",
                provider_user_id=info["sub"],
                provider_user_email=info.get("email"),
                is_primary=True,
            )

        if not user or not user.is_active:
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
        user = await repo.get_by_id(int(user_id))

        if not user:
            raise CredentialsException("User not found")

        return UserProfile(
            id=str(user.id),
            email=user.email,
            name=user.name,
            lastname=user.lastname,
            picture_url=None,
            email_verified=user.email_verified,
            is_active=user.is_active,
            role=None,
            status=None,
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
