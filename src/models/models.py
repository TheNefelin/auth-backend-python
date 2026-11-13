"""Modelos de dominio (SQLAlchemy 2.1).

Todos los modelos viven en este único archivo, igual que `schemas/dtos.py`:
evita imports circulares entre entidades y deja el esquema en un solo lugar.

Mapea `schema_auth.sql`:
- `users`, `user_roles`, `user_status`, `auth_providers`,
  `user_identities`, `user_sessions`, `user_mfa`, `user_recovery_codes`.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

# Convención de nombres para índices y constraints: evita conflictos y hace
# las migraciones predecibles.
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa con convención de nombres (SQLAlchemy 2.0)."""

    metadata = MetaData(naming_convention=naming_convention)


class User(Base):
    """User model representing the 'users' table.

    Perfil principal del usuario, independiente del proveedor de login.
    Incluye soft delete (`deleted_at`) y capacidad de autenticación.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=func.gen_random_uuid())
    email: Mapped[str | None] = Column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = Column(Text, nullable=True)
    name: Mapped[str | None] = Column(String(100), nullable=True)
    lastname: Mapped[str | None] = Column(String(100), nullable=True)
    picture_url: Mapped[str | None] = Column(String(1024), nullable=True)
    email_verified: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    user_role_id: Mapped[int] = Column(Integer, nullable=False)
    status_id: Mapped[int] = Column(Integer, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)

    def can_authenticate(self) -> bool:
        """Check if this user can authenticate (has password or email)."""
        return self.password_hash is not None or self.email is not None


class UserRole(Base):
    """User role model representing the 'user_roles' table."""

    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = Column(String(200), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserStatus(Base):
    """User status model representing the 'user_status' table."""

    __tablename__ = "user_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuthProvider(Base):
    """Auth provider model representing the 'auth_providers' table.

    Solo guarda datos de negocio (name, display_name, is_active). La
    configuración del proveedor (client_id, endpoints) vive en `.env`.
    """

    __tablename__ = "auth_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = Column(String(100), nullable=True)
    is_active: Mapped[bool] = Column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserIdentity(Base):
    """User identity model representing the 'user_identities' table.

    Mapea la tabla 'user_identities' de schema_auth.sql:
    - UUID ids, user_id UUID FK -> users.id
    - provider_id INT FK -> auth_providers(id)
    - columna 'email' para el email del proveedor
    """

    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider_id", "provider_user_id", name="uq_provider_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("auth_providers.id", ondelete="RESTRICT"), nullable=False
    )
    provider_user_id: Mapped[str] = Column(String(255), nullable=False)
    email: Mapped[str | None] = Column(String(255), nullable=True)
    profile_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_primary: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserSession(Base):
    """User session model representing the 'user_sessions' table.

    Represents the 'user_sessions' table storing refresh tokens
    with rotation and revocation support.

    - refresh_token guarda el hash SHA-256 (nunca el token en claro).
    - expires_at = expiración absoluta.
    - last_used_at = última vez usada (control de idle timeout).
    """

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    refresh_token: Mapped[str] = Column(String(512), unique=True, nullable=False)
    expires_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_revoked: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MFA(Base):
    """MFA model representing the 'user_mfa' table.

    Tabla de TOTP (RFC 6238) para segundo factor.
    """

    __tablename__ = "user_mfa"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=func.gen_random_uuid()
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    secret: Mapped[str] = Column(String(255), nullable=False)  # Base32 secret (cifrado en reposo)
    is_enabled: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    enabled_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RecoveryCode(Base):
    """Recovery code model representing the 'user_recovery_codes' table.

    Códigos de recuperación del segundo factor: se guarda el hash, nunca el
    código en texto plano.
    """

    __tablename__ = "user_recovery_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=func.gen_random_uuid()
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    code_hash: Mapped[str] = Column(String(255), nullable=False)  # Hash del código (nunca en texto plano)
    used_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
