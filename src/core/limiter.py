"""Rate limiter (slowapi).

Clave por identidad: si el request trae JWT, el límite es POR USUARIO
(`user:{id}`); si no, por IP. Así un abuso no castiga a todos los usuarios
detrás de la misma IP, ni un usuario puede evadir el límite cambiando de IP.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .security import decode_access_token


def rate_limit_key(request: Request) -> str:
    """Identidad del límite: usuario (si hay JWT válido) o IP."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        try:
            payload = decode_access_token(auth_header.split(" ", 1)[1])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key, default_limits=["100/minute"])
