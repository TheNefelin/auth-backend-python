"""Verificación de tokens de Google contra el endpoint tokeninfo.

Google verifica la firma y los claims del token del lado del servidor.
Único camino para access_token (flujo GIS implícito) e id_token (JWT).

Reglas de aceptación:
- status 200 de tokeninfo (Google valida el token del lado del servidor).
- aud == GOOGLE_CLIENT_ID: sin esto, un token emitido para otra app de
  Google daría acceso a esta.
- email_verified presente y verdadero.
- iss de Google, solo para id_token (JWT). Los access token opacos
  NO llevan/devuelve iss en tokeninfo.

Devuelve el payload del token o None si no es válido / no se puede verificar.
"""

import httpx

from src.core.config import settings

_VALID_ISSUERS = ("accounts.google.com", "https://accounts.google.com")
_TIMEOUT_SECONDS = 10.0


async def verify_google_token(token: str) -> dict | None:
    if not token:
        return None

    # id_token es un JWT (2 puntos); el access_token opaco no.
    param = "id_token" if token.count(".") == 2 else "access_token"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(settings.GOOGLE_TOKEN_INFO_URL, params={param: token})
    except httpx.HTTPError:
        # Red caída, timeout o error de conexión con Google.
        return None

    if response.status_code != 200:
        return None

    data = response.json()

    aud_ok = data.get("aud") == settings.GOOGLE_CLIENT_ID
    # iss solo aplica/existe en id_token; para access token opaco, tokeninfo no lo devuelve.
    iss_ok = (data.get("iss") in _VALID_ISSUERS) if param == "id_token" else True
    email_verified = data.get("email_verified")
    email_verified_ok = str(email_verified).strip().lower() == "true"

    if not (aud_ok and iss_ok and email_verified_ok):
        return None

    return data
