import uuid

from typing import Any
"""User model for the Auth Unificado backend.

Represents the main users table with profile information,
soft delete support, and authentication capabilities.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    """User model representing the 'users' table."""
    
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
    
    # Constraints
    pass
    
    def can_authenticate(self) -> bool:
        """Check if this user can authenticate (has password or email)."""
        return self.password_hash is not None or self.email is not None
