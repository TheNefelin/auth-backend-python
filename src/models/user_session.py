import uuid

from typing import Any
"""User session model for the Auth Unificado backend.

Represents the user_sessions table storing refresh tokens
with rotation and revocation support.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class UserSession(Base):
    """User session model representing the 'user_sessions' table."""
    
    __tablename__ = "user_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=func.gen_random_uuid()
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    refresh_token: Mapped[str] = Column(String(512), unique=True, nullable=False)
    expires_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
