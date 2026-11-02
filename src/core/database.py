"""Database module for the Auth Unificado backend.

Provides SQLAlchemy async engine and session configuration.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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


def get_async_session():
    """Dependency to get an async database session."""
    import asyncio
    
    async def _get_session() -> AsyncSession:
        async with AsyncSessionLocal() as session:
            yield session
    
    return _get_session


async def get_async_engine():
    """Get the async engine instance."""
    return async_engine