"""Dependencies transversales de FastAPI.

Aquí viven las funciones que los endpoints inyectan con `Depends(...)` y que
NO pertenecen a autenticación/autorización (esas están en `security.py`) ni a
la sesión de BD (esa está en `database.py`).
"""

from fastapi import Header

from .config import settings
from .exceptions import InvalidApiKeyError


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verifica la API Key global (header `X-API-Key`)."""
    if x_api_key != settings.API_KEY:
        raise InvalidApiKeyError()
    return True
