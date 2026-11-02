"""Auth provider model for the Auth Unificado backend."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class AuthProvider(Base):
    """Auth provider model representing the 'auth_providers' table."""
    
    __tablename__ = "auth_providers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = Column(String(100), nullable=True)
    is_active: Mapped[bool] = Column(Boolean, nullable=False, default=True)
    config: Mapped[str | None] = Column(String, nullable=True)  # JSON config
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)