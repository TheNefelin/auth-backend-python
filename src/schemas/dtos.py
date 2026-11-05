"""Pydantic schemas/DTOs for the Auth Unificado backend.

Data transfer objects for API requests and responses (Pydantic V2).
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ========== Auth Schemas ==========

class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    lastname: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Formato de email inválido")
        return v.lower()


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
