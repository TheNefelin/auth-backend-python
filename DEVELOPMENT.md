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
| Lenguaje | Python 3.12+ | Planificado |
| Framework | FastAPI | MVP (por implementar) |
| ORM / DB | SQLAlchemy 2.1 (async) + PostgreSQL | MVP (por implementar) |
| Auth | JWT (HS256) + Refresh token rotation | Planificado |
| MFA | TOTP (RFC 6238) + códigos de recuperación | Planificado |
| Tests | pytest | Planificado |
| Variables de entorno | pydantic-settings | Planificado |

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

| Decisión | Justificación |
|----------|---------------|
| Tabla `users` sin `auth_provider` ni `google_sub` | Evitar redundancia; el proveedor se deriva de `user_identities`. |
| Tabla `user_identities` para proveedores federados | Permite múltiples proveedores por usuario. |
| `ON DELETE RESTRICT` en FKs de `users` | Evitar borrado en cascada. Soft delete con `deleted_at`. |
| `client_id` y URLs de endpoints en `.env` | Configuración de la aplicación, no datos de negocio. |
| MFA/2FA con TOTP | Estándar de la industria (RFC 6238). Sin servicios externos. |
| No merge automático por email | Previene *account takeover*. Vinculación solo vía `/auth/connect` autenticada. |

---

## 5. Pendientes (out of scope actual)

- [ ] Implementar backend FastAPI funcional (endpoints `/auth/login`, `/auth/google`, `/auth/github`, `/auth/apple`, `/auth/refresh`, `/auth/logout`, `/auth/connect`, `DELETE /auth/unlink/{provider}`).
- [ ] Configurar `GOOGLE_CLIENT_ID` real en `.env`.
- [ ] Crear base de datos PostgreSQL y ejecutar `schema_auth.sql`.
- [ ] Implementar cambio de correo y cambio de contraseña (`PUT /users/email`, `PUT /users/password`).
- [ ] Implementar flujo "olvidé contraseña".
- [ ] Activar proveedores GitHub y Apple (`is_active = TRUE` en `auth_providers` + endpoints).
- [ ] Implementar MFA/2FA (TOTP + códigos de recuperación).
- [ ] Agregar protección brute-force (lockout de cuenta).
- [ ] Agregar validación de complejidad de contraseña.

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