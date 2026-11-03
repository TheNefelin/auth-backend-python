"""Exceptions module for the Auth Unificado backend.

Custom exception classes for consistent error handling.
"""

from fastapi import HTTPException


class AuthException(HTTPException):
    """Base authentication exception."""
    
    def __init__(self, detail: str = "Authentication failed", status_code: int = 401):
        super().__init__(status_code=status_code, detail=detail)


class UserNotFoundException(AuthException):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            detail=f"User with ID {user_id} not found",
            status_code=404,
        )


class CredentialsException(AuthException):
    """Raised when credentials are invalid."""

    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(
            detail=detail,
            status_code=401,
        )


class TokenExpiredException(AuthException):
    """Raised when a JWT token has expired."""
    
    def __init__(self):
        super().__init__(
            detail="Token has expired",
            status_code=401,
        )


class TokenInvalidException(AuthException):
    """Raised when a JWT token is invalid."""
    
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail=detail, status_code=401)


class PermissionDeniedException(AuthException):
    """Raised when a user doesn't have permission to access a resource."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail, status_code=403)


class ValidationException(HTTPException):
    """Raised for validation errors."""
    
    def __init__(self, detail: str):
        super__(status_code=422, detail=detail)