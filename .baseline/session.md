# Sesión — backend-python

> Checkpoint local (fuera de Git): el punto de continuación de la tarea en curso, no un diario.
> Manténlo corto (≤ ~40 líneas) y reemplaza su contenido en vez de acumular. Sin transcripciones ni secretos.

## Tarea activa

Core backend en estado senior + auth Google/register/login local. Suite en verde.

## Último avance comprobado

- **Core refactorizado (bloques 0-3)**:
  - Error unificado **RFC 9457** (`fastapi-problem` + `rfc9457`); excepciones semánticas en `core/exceptions.py`; handler global en `main.py`.
  - `core/` separado: `dependencies.py` = solo `verify_api_key` (sin conectar); auth en `security.py` (`get_current_user`, `require_user/admin`); `get_db` en `database.py`; `roles.py` (enum) + `startup.py` (valida roles al arrancar).
  - Refresh: rotación **atómica** + **detección de reuso** (revoca familia). Rate limit real (`slowapi`, por usuario/IP).
  - Hashing `pwdlib[bcrypt]` (passlib eliminado). Pydantic V2, SQLAlchemy 2.0 (`DeclarativeBase`). DTOs muertos eliminados.
- **Register local e2e**: hash + identidad `local` + auto-login (tokens); 409 si email existe (sin merge); validaciones email/password (8-128). Verificado con TestClient.
- **Login local**: verifica password + estado (`UserStatusRepository`), emite tokens.
- **Tests backend 32/32** (`pytest`, unitarios sin BD). Entorno: `.venv` aislado — activar para todo.

## Pendientes

- GitHub / Apple; `/auth/connect`; verificación de email; `verify_api_key` (contexto por definir).
- `.env.demo`: `DEBUG`/`API_KEY` sin consumidor. Tests de integración (BD real).
- `docs/auth-flow.md` §9 tiene el roadmap completo.
