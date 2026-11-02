"""User identity model for the Auth Unificado backend.

Represents the user_identities table linking users to external
auth providers (Google, GitHub, Apple, etc.).
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class UserIdentity(Base):
    """User identity model representing the 'user_identities' table."""
    
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider_id", "provider_user_id", name="uq_provider_user"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_id: Mapped[str] = Column(String(50), nullable=False)  # 'local', 'google', 'github', 'apple'
    provider_user_id: Mapped[str] = Column(String(255), nullable=False)  # sub, github_id, apple_id, etc.
    provider_user_email: Mapped[str | None] = Column(String(255), nullable=True)
    is_primary: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    is_email_verified: Mapped[bool] = Column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)