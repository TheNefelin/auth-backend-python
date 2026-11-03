"""User identity model for the Auth Unificado backend.

Mapea la tabla 'user_identities' de schema_auth.sql:
- UUID ids, user_id UUID FK -> users.id
- provider_id INT FK -> auth_providers(id)
- columna 'email' para el email del proveedor
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class UserIdentity(Base):
    """User identity model representing the 'user_identities' table."""

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
