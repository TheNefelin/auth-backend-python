# Sesión — backend-python

> Checkpoint local (fuera de Git): el punto de continuación de la tarea en curso, no un diario.
> Mantenlo corto (≤ ~40 líneas) y reemplaza su contenido en vez de acumular. Sin transcripciones ni secretos.

## Tarea activa

Auth Google e2e funcionando + suite de tests (front y back) en verde.

## Último avance comprobado

- **Tests backend 31/31** (`pytest`, unitarios sin BD): security, google_service, dependencies (roles), auth_service (refresh: rotación/idle/absoluto). Config en `pytest.ini`. Eliminado `test_google_auth.py` obsoleto.
- **Tests frontend 18/18** (`ng test`, vitest): auth-store, auth-guard, auth-interceptor, user-details.
- **Hashing migrado `passlib` → `pwdlib[bcrypt]`** (`security.py` usa `PasswordHash((BcryptHasher(),))`). passlib está abandonado e incompatible con bcrypt≥4.1; destapado por los tests.
- **README backend reescrito**: alineado a la realidad (JWT_*, pwdlib, schema en backend-python, endpoints reales, regla del venv, sección Tests). Eliminada basura de sesión previa.
- Entorno: UN solo Python (3.14.7) + venv aislado. Regla: activar `.venv` para todo. Deps: `pwdlib[bcrypt] bcrypt pytest pytest-asyncio`.
- Login Google e2e, refresh, guard, logout server-side: OK (usuarios). Frontend commiteado por el usuario.

## Pruebas ejecutadas y resultado real

- `pytest` → 31 passed. `ng test --watch=false` → 18 passed. Registro real de ambas corridas.

## Siguiente paso

- Frontend: guardar `refresh_token` (store), authInterceptor 401→refresh→retry, logout limpia ambos tokens.
- Pendientes previos: `ValidationException.super__` typo, `.env.demo` DEBUG/API_KEY, `verify_api_key_header` (2º round), tests.

## Archivos tocados (tras el último commit)

- `src/core/dependencies.py`, `src/api/auth/service.py`, `src/api/auth/repository.py`

## Pruebas ejecutadas y resultado real

- `import src.api.auth.routes` OK; TestClient: GET /me 200/401/401 con perfil real. Boot OK.

## Bloqueos

- Ninguno.

## Siguiente paso (backend)

- Ampliar `/auth/google`: `provider` + `user` (contrato para `UserDetailsComponent`); `picture_url`/name refresh por login (userinfo); `ValidationException.super__` typo (línea 64, sin uso); `.env.demo`: `DEBUG=True` y `API_KEY=TestingApiKey` sin consumidor; `refresh` stub; `/register` e2e sin probar.
