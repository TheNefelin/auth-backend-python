"""Pydantic schemas/DTOs for the Auth Unificado backend.

Data transfer objects for API requests and responses (Pydantic V2).
"""

from datetime import datetime, timezone
from typing import Optional
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


# ========== Auth Schemas ==========

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserRegister(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = None
    lastname: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Formato de email inválido")
        return v


class AuthGoogleRequest(BaseModel):
    """Google login request (GIS implicit flow, access_token del frontend)."""

    googleToken: str = Field(
        ...,
        min_length=1,
        description="access_token o id_token emitido por Google Identity Services",
    )


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    lastname: Optional[str] = None
    picture_url: Optional[str] = None
    email_verified: bool = False
    is_active: bool = True
    role: Optional[str] = None
    status: Optional[str] = None
    provider: Optional[str] = None


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 900


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token emitido en el login")
