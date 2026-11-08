# Sesión — backend-python

> Checkpoint local (fuera de Git): el punto de continuación de la tarea en curso, no un diario.
> Mantenlo corto (≤ ~40 líneas) y reemplaza su contenido en vez de acumular. Sin transcripciones ni secretos.

## Tarea activa

Backend completo para MVP. Auth Google + login clásico + registro. API Key exigida en toda la API. Logging de seguridad. Suite en verde.

## Último avance comprobado

- **Auth**: Google login, `/auth/login`, `/auth/register`, `/auth/me`, `/auth/refresh`, `/auth/logout`.
- **Seguridad**: `verify_api_key` a nivel de router (router-level, `compare_digest`); toda la API exige `X-API-Key`. `/health` y `/docs` sin Key.
- **Logging**: eventos de seguridad registrados (login fallido, Google token inválido, reuso, API Key inválida). `LOG_LEVEL` configurable.
- **Roles**: enum = contrato + validación al arranque contra `user_roles`.
- **Refresh**: rotación atómica + detección de reuso + idle/absoluto timeout.
- **Verificado**: `pytest` **50/50**, build OK.

## Pendientes

- GitHub / Apple (stubs; replicar patrón de Google).
- `/auth/connect` + `/auth/unlink` (unificar cuentas federadas).
- Verificación de email (`email_verified` real).
- MFA/2FA (TOTP + códigos de recuperación).
- Cambio de correo/contraseña, "olvidé contraseña", brute-force.
- Alertas de seguridad (hoy solo logs a stdout).
- Endurecer `style-src` en el CSP (riesgo bajo, aceptado por la industria).

## Nota

Proyecto listo para MVP. Backend y frontend commiteados y al día.