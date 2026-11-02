import uuid

from typing import Any
"""MFA/2FA model for the Auth Unificado backend.

Represents the user_mfa and user_recovery_codes tables
for TOTP-based multi-factor authentication.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class MFA(Base):
    """MFA model representing the 'user_mfa' table."""
    
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
    """Recovery code model representing the 'user_recovery_codes' table."""
    
    __tablename__ = "user_recovery_codes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=func.gen_random_uuid()
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    code_hash: Mapped[str] = Column(String(255), nullable=False)  # Hash del código (nunca en texto plano)
    used_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
