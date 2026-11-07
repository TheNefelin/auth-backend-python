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
| Auth | Google + registro/login local; JWT (HS256) + refresh rotativo con idle timeout | Implementado |
| Hashing | `pwdlib` + `bcrypt` | Implementado (passlib eliminado) |
| MFA | TOTP (RFC 6238) | Planificado |
| Tests | pytest (unitarios, sin BD) | 32/32 |
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
| Refresh token: hash SHA-256, rotación **atómica** + detección de reuso, absoluto + idle | Nunca en claro; la sesión no es eterna; un token reusado revoca la familia. | Aceptado |
| Hashing con `pwdlib[bcrypt]` | passlib está abandonado e incompatible con bcrypt ≥4.1. | Aceptado |
| Errores RFC 9457 (`fastapi-problem`) con excepciones semánticas | Formato único y estándar; nada de `HTTPException` ad-hoc. | Aceptado |
| `core/` separado: `security`(auth + API key), `database`(get_db), `roles`(enum), `startup`(valida roles) | Una responsabilidad por módulo. | Aceptado |
| Roles: enum = contrato + validación al arranque contra `user_roles` | Evita fallo silencioso si la BD diverge. | Aceptado |
| Rate limit por identidad (`slowapi`: usuario/IP) | Protección de fuerza bruta sin castigar por IP compartida. | Aceptado |
| No merge automático por email | Previene *account takeover*. Vinculación explícita (futuro `/auth/connect`). | Aceptado |

---

## 5. Pendientes

- [ ] GitHub y Apple (stubs; replicar el patrón de Google).
- [ ] `/auth/connect` + `/auth/unlink` (unificar cuentas federadas).
- [ ] Verificación de email (`email_verified` real).
- [x] `verify_api_key`: conectado a nivel de router (`secrets.compare_digest`); toda la API exige `X-API-Key`.
- [ ] MFA/2FA (TOTP + códigos de recuperación).
- [ ] Cambio de correo/contraseña, "olvidé contraseña", brute-force.
- [x] Tests de integración (BD real): 50 tests, rollback por test.
- [ ] Alertas de seguridad (hoy solo logs a stdout).

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