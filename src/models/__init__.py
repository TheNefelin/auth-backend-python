"""Base model class for SQLAlchemy ORM."""

from .base import Base


# Import all models to register them
from .user import User
from .user_role import UserRole
from .user_status import UserStatus
from .auth_provider import AuthProvider
from .user_identity import UserIdentity
from .user_session import UserSession
from .mfa import MFA, RecoveryCode  # noqa: F401