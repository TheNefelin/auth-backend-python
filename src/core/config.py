"""Configuration module for the Auth Unificado backend.

.env es la única fuente de verdad de la configuración:
- Las variables requeridas no tienen default y fallan al arrancar con un
  mensaje claro (nunca valores hardcodeados ni secretos ficticios).
- CORS_ORIGINS vacío/ausente significa "sin orígenes cross-origin
  permitidos"; no se sustituye por una lista por defecto.
"""

import json
import os

from dotenv import load_dotenv

# Carga el .env de la raíz del backend (búsqueda ascendente desde este archivo).
# Las variables ya presentes en el entorno tienen prioridad (override=False).
load_dotenv()


def _required(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise RuntimeError(
			f"Falta la variable de entorno requerida: {name}. "
			"Defínela en tu .env (ver .env.demo)."
		)
	return value


def _parse_cors_origins() -> list[str]:
	raw = os.getenv("CORS_ORIGINS", "").strip()
	if not raw:
		# Vacío = ningún origen cross-origin permitido.
		return []
	try:
		origins = json.loads(raw)
	except json.JSONDecodeError as exc:
		raise RuntimeError(
			f"CORS_ORIGINS no es JSON válido: {raw!r}. "
			'Esperado un arreglo, p. ej.: ["http://localhost:4200"]'
		) from exc
	if not isinstance(origins, list) or not all(isinstance(o, str) for o in origins):
		raise RuntimeError("CORS_ORIGINS debe ser un arreglo JSON de strings.")
	return origins


class Settings:
	"""Application settings. .env manda; lo que falta, falla."""

	# Application
	APP_NAME: str = "auth-unificado-backend"
	APP_VERSION: str = "1.0.0"

	# Database
	DATABASE_URL: str = _required("DATABASE_URL")

	# JWT
	JWT_SECRET_KEY: str = _required("JWT_SECRET_KEY")
	JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
	JWT_ACCESS_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "15"))
	JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))
	JWT_REFRESH_IDLE_MINUTES: int = int(os.getenv("JWT_REFRESH_IDLE_MINUTES", "30"))

	# Google OAuth ("" = no configurado)
	GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
	GOOGLE_TOKEN_INFO_URL: str = os.getenv("GOOGLE_TOKEN_INFO_URL", "https://oauth2.googleapis.com/tokeninfo")
	GOOGLE_USERINFO_URL: str = os.getenv("GOOGLE_USERINFO_URL", "https://www.googleapis.com/oauth2/v3/userinfo")

	# Rate limiting
	RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
	RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

	# API Key del BFF (header X-API-Key). REQUERIDA: si falta, el arranque falla.
	# Un default vacío permitiría que una clave vacía pasara la verificación.
	API_KEY: str = _required("API_KEY")

	# Logging
	LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

	# CORS
	CORS_ORIGINS: list[str] = _parse_cors_origins()


# Global instance for easy import
settings = Settings()
