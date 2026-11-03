"""Configuration module for the Auth Unificado backend.

Provides application settings loaded from environment variables.
Loads .env via python-dotenv before reading any variable.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

# Carga el .env de la raíz del backend (búsqueda ascendente desde este archivo).
# Variables ya presentes en el entorno tienen prioridad (override=False por defecto).
load_dotenv()


@lru_cache()
def get_settings() -> "Settings":
    """Get application settings from environment variables."""
    return Settings()


class Settings:
    """Pydantic-like settings class loaded from environment variables."""
    
    # Application
    APP_NAME: str = "auth-unificado-backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/auth_db")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_TOKEN_INFO_URL: str = os.getenv("GOOGLE_TOKEN_INFO_URL", "https://oauth2.googleapis.com/tokeninfo")
    GOOGLE_USERINFO_URL: str = os.getenv("GOOGLE_USERINFO_URL", "https://www.googleapis.com/oauth2/v3/userinfo")
    GOOGLE_ISSUER: str = os.getenv("GOOGLE_ISSUER", "https://accounts.google.com")
    GOOGLE_SCOPE: str = os.getenv("GOOGLE_SCOPE", "openid email profile")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:4200", "http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:5500", "http://localhost:4321"]
    
    @property
    def is_development(self) -> bool:
        return self.DEBUG or not self.BACKEND_CORS_ORIGINS


# Global instance for easy import
settings = get_settings()