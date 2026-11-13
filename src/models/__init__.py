"""Modelos de dominio (SQLAlchemy 2.1).

Fachada del paquete: reexporta los modelos definidos en `models.py` para que
`from src.models import User` funcione en todo el código, e importa todos los
modelos para registrarlos en `Base.metadata`.
"""

from .models import (
    MFA,
    AuthProvider,
    Base,
    RecoveryCode,
    User,
    UserIdentity,
    UserRole,
    UserSession,
    UserStatus,
)

__all__ = [
    "MFA",
    "AuthProvider",
    "Base",
    "RecoveryCode",
    "User",
    "UserIdentity",
    "UserRole",
    "UserSession",
    "UserStatus",
]
