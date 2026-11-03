# Sesión — backend-python

> Checkpoint local (fuera de Git): el punto de continuación de la tarea en curso, no un diario.
> Mantenlo corto (≤ ~40 líneas) y reemplaza su contenido en vez de acumular. Sin transcripciones ni secretos.

## Tarea activa

AUTH Google — el login funciona extremo a extremo (verificado por el usuario). `google_service.py` sin diagnósticos.

## Último avance comprobado

- Config: `get_settings()`/`@lru_cache` eliminados → `settings = Settings()` directo. `.env` es fuente de verdad (required DATABASE_URL/JWT_SECRET_KEY, CORS_ORIGINS desde .env; SIN variables durísimas; vocabulario JWT_*). `.env.demo` alineado (GOOGLE_CLIENT_ID real). `main.py`: CORS desde settings.
- `dtos.py`: DTOs muertos `GoogleTokenInfo`/`GoogleUserInfo` eliminados.
- `get_db()` hace commit al final de la request (persistencia real de /auth/google). `AuthService`, `google_service.py`, `models/*`, `routes.py` corregidos según esquema DDL real. Login Google funciona end-to-end (usuario).
- Único sin commitear: este cleanup (config + dtos).

## Pruebas ejecutadas y resultado real

- Boot real OK (`import routes`); 6 rutas; sin referencias colgadas; persistencia validada por el usuario (fila en users tras re-login post-fix `get_db`).
- Pendiente menor: `GOOGLE_CLIENT_ID` del `.env` coincide con el del frontend (aud OK — confirmado por el usuario). JWT_SECRET_KEY del .env no verificada (última medición: `False`/default inseguro).

## Archivos tocados (tras el último commit)

- `src/api/auth/google_service.py` (eliminados logs de diagnóstico)

## Pruebas ejecutadas y resultado real

- Import + rutas OK tras la limpieza. Login e2e: éxito reportado por el usuario (no ejecutado por el asistente).

## Bloqueos

- Ninguno.

## Siguiente paso

- Fase 2: `/auth/me` (UserProfile) y `/refresh` usan `is_active` inexistente → reescribir contra el DDL (status_id/can_authenticate); `ValidationException.super__` typo; `picture_url` de Google sin usar; frontend: logout de home no limpia JWT.
