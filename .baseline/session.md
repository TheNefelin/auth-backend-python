# Sesión — backend-python

> Checkpoint local (fuera de Git): el punto de continuación de la tarea en curso, no un diario.
> Mantenlo corto (≤ ~40 líneas) y reemplaza su contenido en vez de acumular. Sin transcripciones ni secretos.

## Tarea activa

MVP completo y verificado. Última tarea: normalización de imports del backend (todo al inicio del módulo, una línea por import).

## Último avance comprobado

- **Imports normalizados**: `src/api/auth/service.py`, `src/api/auth/repository.py`, `tests/conftest.py`. Cero imports dentro de funciones. Alias `UI`/`US`/`UserModel` eliminados; imports muertos (`get_db`, `Token`) fuera; `UserProfile` duplicado corregido.
- **Importante**: `service.py` importa `google_service` como módulo (`from . import google_service`), no sus funciones. Los tests parchean `src.api.auth.google_service.<fn>`; ligar la función al namespace rompe el mock (rompió 1 test al subir el import).
- **Auth**: Google login, `/auth/login`, `/auth/register`, `/auth/me`, `/auth/refresh`, `/auth/logout`.
- **Seguridad**: `verify_api_key` a nivel de router (toda la API exige `X-API-Key`); `/health` y `/docs` sin Key. Logging de eventos de seguridad.
- **Roles**: enum = contrato + validación al arranque contra `user_roles`.
- **Refresh**: rotación atómica + detección de reuso + idle/absoluto timeout.
- **Verificado**: `pytest` **50/50** (exit 0) y `from src.main import app` importa sin ciclos.

## Pendientes

- GitHub / Apple (sin stub en backend).
- `/auth/connect` + `/auth/unlink` (unificar cuentas federadas).
- Verificación de email (`email_verified` real).
- MFA/2FA (TOTP + códigos de recuperación): tablas creadas, falta la lógica.
- Cambio de correo/contraseña y flujo "olvidé contraseña".
- Alertas de seguridad (hoy solo logs a stdout).
- El service consulta entidades ORM directamente → mover al repository (skill `fastapi` §4.2).
- Endurecer `style-src` en la CSP.

## Nota

`pytest.ini` ya trae `addopts = -q`: pasar `-q` otra vez lo convierte en `-qq` y oculta la línea "N passed". Correr `python -m pytest` a secas.
