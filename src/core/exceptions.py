"""Excepciones semánticas del backend (RFC 9457 / Problem Details).

Todas heredan de las clases de `rfc9457` y se serializan como
`{type, title, status, detail}` mediante el handler global de `main.py`
(`fastapi-problem`). Las reglas de negocio lanzan ESTAS excepciones,
nunca `HTTPException`.

Patrón basado en las referencias del autor (portfolio-python,
game_guides_python, biblioteca-wallmapu-python).
"""

from fastapi import status
from rfc9457 import (
    BadRequestProblem,
    ConflictProblem,
    ForbiddenProblem,
    NotFoundProblem,
    Problem,
    UnauthorisedProblem,
)


class AppError(Problem):
    """Error de negocio base (RFC 9457).

    Se serializa como `{type, title, status, detail}` y el handler global de
    `main.py` lo convierte a una respuesta `application/problem+json`.
    """

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        super().__init__(title=message, detail=message, status=status_code, type_="app-error")


class NotFoundError(NotFoundProblem):
    type_ = "not-found"
    title = "Resource not found."

    def __init__(self, entity: str = "Recurso"):
        super().__init__(detail=f"{entity} no encontrado")
        self.message = self.detail


class ConflictError(ConflictProblem):
    type_ = "conflict"
    title = "Resource conflict."

    def __init__(self, message: str = "El recurso ya existe"):
        super().__init__(detail=message)
        self.message = message


class UnauthorizedError(UnauthorisedProblem):
    type_ = "unauthorized"
    title = "Unauthorized."

    def __init__(self, message: str = "Token inválido o expirado"):
        super().__init__(detail=message)
        self.message = message


class ForbiddenError(ForbiddenProblem):
    type_ = "forbidden"
    title = "Forbidden."

    def __init__(self, message: str = "No tienes permisos para realizar esta acción"):
        super().__init__(detail=message)
        self.message = message


class InvalidApiKeyError(UnauthorisedProblem):
    type_ = "invalid-api-key"
    title = "Invalid API key."

    def __init__(self, message: str = "API Key inválida"):
        super().__init__(detail=message)
        self.message = message
