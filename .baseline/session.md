# Sesión — backend-python

> Checkpoint local (fuera de Git): el punto de continuación de la tarea en curso, no un diario.
> Mantenlo corto (≤ ~40 líneas) y reemplaza su contenido en vez de acumular. Sin transcripciones ni secretos.

## Tarea activa

AUTH Google completo extremo a extremo (login + `/auth/me`). Usuario construye `user-details-component` en el frontend.

## Último avance comprobado

- `/auth/me` FUNCIONA de punta a punta (verificado E2E con TestClient): 200 con perfil real (`email`, `role=user`, `status=activo`, `email_verified=true`, `picture_url=null`), 401 sin token, 401 con token malformado (antes 500).
- `core/dependencies.py`: `get_current_user` reescrito — `HTTPBearer` (antes query param `authorization`), `uuid.UUID(sub)` (antes string crudo → asyncpg error), import `src.models` (antes `.models` inexistente), decode de JWT envuelto en 401 (antes ValueError cruda → 500 sin CORS).
- `service.get_profile`: `int()` → `uuid.UUID`; enriquecido con `picture_url` + `role`/`status` desde BD (nuevos `UserRoleRepository.get_by_id` y `UserStatusRepository.get_by_id`).
- Login Google completo OK (usuario en navegador + fila en BD confirmada read-only).

## Archivos tocados (tras el último commit)

- `src/core/dependencies.py`, `src/api/auth/service.py`, `src/api/auth/repository.py`

## Pruebas ejecutadas y resultado real

- `import src.api.auth.routes` OK; TestClient: GET /me 200/401/401 con perfil real. Boot OK.

## Bloqueos

- Ninguno.

## Siguiente paso (backend)

- Ampliar `/auth/google`: `provider` + `user` (contrato para `UserDetailsComponent`); `picture_url`/name refresh por login (userinfo); `ValidationException.super__` typo (línea 64, sin uso); `.env.demo`: `DEBUG=True` y `API_KEY=TestingApiKey` sin consumidor; `refresh` stub; `/register` e2e sin probar.
