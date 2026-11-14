"""Database module for the Auth Unificado backend.

Provides SQLAlchemy async engine, session configuration and the `get_db`
dependency (una transacción por request).
"""

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Convención de nombres para índices y constraints: evita conflictos y hace
# las migraciones predecibles. Una sola Base para todo el proyecto (catálogo
# agent-baseline §5 Modelos).
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
