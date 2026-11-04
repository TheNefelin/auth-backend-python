"""User session model for the Auth Unificado backend.

Represents the 'user_sessions' table storing refresh tokens
with rotation and revocation support.

- refresh_token guarda el hash SHA-256 (nunca el token en claro).
- expires_at = expiración absoluta.
- last_used_at = última vez usada (control de idle timeout).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class UserSession(Base):
    """User session model representing the 'user_sessions' table."""

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
