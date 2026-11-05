"""Database module for the Auth Unificado backend.

Provides SQLAlchemy async engine, session configuration and the `get_db`
dependency (una transacción por request).
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True,
)

# Create session maker
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency de sesión de BD: una transacción por request.

    El repository solo hace `flush()`. Aquí se hace commit al final de la
    request (persiste lo flusheado) y rollback si hubo una excepción, para
    que la request sea atómica (p. ej. usuario + identidad juntos o ninguno).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
