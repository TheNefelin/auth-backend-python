# DEVELOPMENT.md — Mapa del proyecto backend-python (Auth Unificado MVP)

Este archivo es la memoria viva del backend. Se actualiza solo con decisiones que sobreviven a la sesión. No es un diario.

---

## 1. Propósito

Backend de autenticación transversal que soporta:
- Email + contraseña (local)
- Google (activo)
- GitHub y Apple (registrados pero inactivos, listos para activar)
- MFA/2FA con TOTP + códigos de recuperación

---

## 2. Stack

| Capa | Tecnología | Estado |
|------|-----------|--------|
| Lenguaje | Python 3.14 (venv `.venv`) | En uso |
| Framework | FastAPI | Google funcional |
| ORM / DB | SQLAlchemy 2.1 (async) + PostgreSQL | En uso |
| Auth | JWT (HS256) + refresh rotativo con idle timeout | Implementado |
| Hashing | `pwdlib` + `bcrypt` | Implementado (passlib eliminado) |
| MFA | TOTP (RFC 6238) | Planificado |
| Tests | pytest (unitarios, sin BD) | 31/31 |
| Config | `.env` cargado con python-dotenv (clase propia) | En uso |

---

## 3. Estructura de carpetas (propuesta)

```
backend-python/
├── DEVELOPMENT.md          ← este archivo
├── AGENTS.md               ← reglas de operación
├── SKILL.md                ← reglas del stack FastAPI
├── .baseline/              → baseline propio
│   ├── AGENTS.md
│   ├── session.md
│   └── skills/fastapi, sql
├── run.py                  → punto de entrada (uvicorn)
├── requirements.txt        → dependencias
├── .env / .env_demo        → variables de entorno (plantilla)
├── .gitignore
├── pytest.ini
├── src/
│   ├── main.py             → app FastAPI
│   ├── api/
│   │   ├── auth/           → login local, Google, GitHub, Apple, refresh, logout, connect
│   │   ├── users/          → perfil, email, contraseña
│   │   ├── user_identities/→ identidades federadas (sin routes)
│   │   └── user_sessions/  → refresh tokens (sin routes)
│   ├── core/               → config, database, security, exceptions, logger, limiter, dependencies
│   ├── models/             → modelos de dominio
│   └── schemas/            → DTOs Pydantic
├── tests/
│   └── test_auth.py
└── static/                 → archivos estáticos
```

---

## 4. Decisiones de diseño (aceptadas)

| Decisión | Justificación | Estado |
|----------|---------------|--------|
| Tabla `users` sin `auth_provider` ni `google_sub` | Evitar redundancia; el proveedor se deriva de `user_identities`. | Aceptado |
| `user_identities` para proveedores federados (`provider_id` INT FK al catálogo) | Permite múltiples proveedores por usuario. | Aceptado |
| `ON DELETE RESTRICT` en FKs de `users` | Evitar borrado en cascada. Soft delete con `deleted_at`. | Aceptado |
| `client_id` y URLs de endpoints en `.env` | Configuración, no datos de negocio. | Aceptado |
| `get_db()` hace commit/rollback por request | Antes nada persistía; atómico para user + identity. | Aceptado |
| Refresh token: hash SHA-256, rotación, expiración absoluta + idle timeout | Nunca se guarda el token en claro; la sesión no es eterna. | Aceptado |
| Hashing con `pwdlib[bcrypt]` | passlib está abandonado e incompatible con bcrypt ≥4.1. | Aceptado |
| `require_user`/`require_admin` leen el rol de la BD | El token identifica; el permiso se resuelve en servidor. | Aceptado |
| No merge automático por email | Previene *account takeover*. Vinculación explícita (futuro `/auth/connect`). | Aceptado |

---

## 5. Pendientes

- [ ] `/auth/login` y `/auth/register` (email+contraseña): lógica parcial, sin verificar.
- [ ] GitHub y Apple (stubs; replicar el patrón de Google).
- [ ] Detección de reuso del refresh token (revocar la familia).
- [ ] Rate limiting en login; API Key global (`verify_api_key_header`).
- [ ] MFA/2FA (TOTP + códigos de recuperación).
- [ ] Cambio de correo/contraseña, flujo "olvidé contraseña", brute-force, `/auth/connect` + `/auth/unlink`.
- [ ] Deuda: `@validator`→`@field_validator` (Pydantic V2), `declarative_base`→`orm.declarative_base`, `ValidationException.super__` (typo), `.env.demo` (`DEBUG`/`API_KEY` sin consumidor).

---

## 6. Reglas del proyecto (baseline)

- Idioma: español neutro, sin voseo.
- Seguridad primero: nunca guardar secretos en BD ni en código.
- No sobreingeniería: solo lo necesario para el requisito actual.
- Evidencia: no afirmar comportamientos sin verificar.
- El usuario ejecuta git commit; el agente solo propone mensajes.

---

## 7. Notas

- Los proyectos originales (`biblioteca-wallmapu-python` y `game_guides_python`) **no fueron modificados**.
- Antes de ejecutar `schema_auth.sql`, asegurate de tener tu **GOOGLE_CLIENT_ID** real en `.env`. El `client_id` ya no va en la BD.
- Compatible con PostgreSQL.