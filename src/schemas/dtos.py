"""Pydantic schemas/DTOs for the Auth Unificado backend.
Data transfer objects for API requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ========== User Management Schemas ==========

class UserCreate(BaseModel):
    """User creation schema."""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    name: Optional[str] = Field(None, max_length=100, description="User name")
    lastname: Optional[str] = Field(None, max_length=100, description="User lastname")
    
    @validator("email")
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[str] = Field(None, description="User email")
    name: Optional[str] = Field(None, max_length=100, description="User name")
    lastname: Optional[str] = Field(None, max_length=100, description="User lastname")
    
    @validator("email", pre=True)
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class APIResponse(BaseModel):
    """Generic API response schema."""
    success: bool = Field(True, description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# ========== Provider Link/Unlink Schemas ==========

class ProviderLinkRequest(BaseModel):
    """Request to link a provider to a user."""
    provider: str = Field(..., description="Provider name ('google', 'github', 'apple')")
    token: str = Field(..., description="OAuth token from provider")
    
    @validator("provider")
    def validate_provider(cls, v: str) -> str:
        allowed = ["google", "github", "apple"]
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v


class ProviderUnlinkRequest(BaseModel):
    """Request to unlink a provider from a user."""
    provider: str = Field(..., description="Provider name to unlink")
    
    @validator("provider")
    def validate_provider(cls, v: str) -> str:
        allowed = ["google", "github", "apple"]
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v


# ========== MFA Schemas ==========

class MFASetup(BaseModel):
    """MFA setup request schema."""
    provider: str = Field("totp", description="MFA provider")
    
    @validator("provider")
    def validate_provider(cls, v: str) -> str:
        if v != "totp":
            raise ValueError("Only TOTP provider supported")
        return v


class MFATotpVerify(BaseModel):
    """MFA TOTP verification schema."""
    code: str = Field(..., min_length=6, max_length=6, description="TOTP code")


class MFAEnable(BaseModel):
    """MFA enable response schema."""
    secret: str = Field(..., description="Base32 secret for TOTP")
    qr_code_url: str = Field(..., description="QR code URL for authenticator app")


class RecoveryCodeVerify(BaseModel):
    """Recovery code verification schema."""
    code: str = Field(..., min_length=8, max_length=8, description="Recovery code")

# ========== Auth Schemas ==========
class UserLogin(BaseModel):
    email: str
    password: str


class AuthGoogleRequest(BaseModel):
    """Google login request (GIS implicit flow, access_token del frontend)."""

    googleToken: str = Field(
        ...,
        min_length=1,
        description="access_token o id_token emitido por Google Identity Services",
    )


class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    lastname: Optional[str] = None


class UserProfile(BaseModel):
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

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 900
