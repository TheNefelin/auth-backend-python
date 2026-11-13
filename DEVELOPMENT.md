# DEVELOPMENT.md — Mapa del proyecto auth-backend-python (Auth Unificado MVP)

Memoria viva del backend. Solo decisiones que sobreviven a la sesión. No es un diario.

---

## 1. Propósito

Backend de autenticación transversal: email + contraseña (local), Google (activo), GitHub y Apple (pendientes), MFA/2FA (pendiente).

---

## 2. Stack

| Capa | Tecnología | Estado |
|------|-----------|--------|
| Lenguaje | Python 3.14 (venv `.venv`) | En uso |
| Framework | FastAPI | Google funcional |
| ORM / DB | SQLAlchemy 2.1 (async) + PostgreSQL | En uso |
| Auth | Google + registro/login local; JWT (HS256) + refresh rotativo con idle timeout | Implementado |
| Hashing | `pwdlib` + `bcrypt` | Implementado (passlib eliminado) |
| API Key | Global, a nivel de router (`X-API-Key`) | Implementado |
| MFA | TOTP (RFC 6238) | Pendiente (tablas creadas) |
| Tests | pytest (unitarios + integración con BD real) | 50/50 |
| Config | `.env` con python-dotenv | En uso |

---

## 3. Estructura de carpetas

```
auth-backend-python/
├── DEVELOPMENT.md, AGENTS.md, SKILL.md   ← memoria, reglas, skill del stack
├── .baseline/          → AGENTS.md, session.md, skills/
├── run.py              → uvicorn src.main:app (127.0.0.1:8000)
├── pytest.ini          → pythonpath, asyncio_mode, testpaths
├── vercel.json         → despliegue serverless
├── .env / .env.demo    → variables de entorno (plantilla versionada)
├── schema_auth.sql     → modelo de tablas PostgreSQL + seeds
├── src/
│   ├── main.py         → app FastAPI, middlewares, handlers RFC 9457
│   ├── api/auth/       → única feature: routes, service, repository, google_service
│   ├── core/           → config, database, dependencies, exceptions, security,
│   │                     logger, limiter, roles, startup
│   ├── models/         → user, user_role, user_status, auth_provider,
│   │                     user_identity, user_session, mfa, base
│   └── schemas/dtos.py → DTOs Pydantic v2
└── tests/              → conftest (BD real, rollback por test) + 5 test_*.py
```

---

## 4. Decisiones de diseño (aceptadas)

| Decisión | Justificación | Estado |
|----------|---------------|--------|
| `users` sin `auth_provider` ni `google_sub` | El proveedor se deriva de `user_identities`; evita redundancia. | Aceptado |
| `user_identities` para proveedores federados | Permite varios proveedores por usuario. | Aceptado |
| `ON DELETE RESTRICT` en FKs de `users` | Sin borrado en cascada; soft delete con `deleted_at`. | Aceptado |
| `client_id` y URLs en `.env` | Configuración, no datos de negocio. | Aceptado |
| `get_db()` hace commit/rollback por request | Atómico para user + identity. | Aceptado |
| Refresh: hash SHA-256, rotación **atómica** + detección de reuso, absoluto + idle | Nunca en claro; un token reusado revoca la familia. | Aceptado |
| Hashing con `pwdlib[bcrypt]` | passlib está abandonado e incompatible con bcrypt ≥4.1. | Aceptado |
| Errores RFC 9457 (`fastapi-problem`) | Formato único; nada de `HTTPException` ad-hoc. | Aceptado |
| `core/` separado: `security`, `database`, `dependencies`, `roles`, `startup` | Una responsabilidad por módulo. | Aceptado |
| Roles: enum = contrato + validación al arranque | Evita fallo silencioso si la BD diverge. | Aceptado |
| Rate limit por identidad (`slowapi`) | Fuerza bruta sin castigar por IP compartida. | Aceptado |
| API Key global a nivel de router (`X-API-Key`) | Ninguna ruta nueva queda desprotegida por descuido. | Aceptado |
| No merge automático por email | Previene *account takeover*. Vinculación explícita (`/auth/connect`). | Aceptado |
| Imports al inicio del módulo | Grafo de dependencias visible; `models ← core ← api` no tiene ciclos. | Aceptado |
| `service.py` importa `google_service` como módulo | Los tests parchean `src.api.auth.google_service.<fn>`; ligar la función rompe el mock. | Aceptado |

---

## 5. Pendientes

- [ ] GitHub y Apple (replicar el patrón de Google; sin stub en backend).
- [ ] `/auth/connect` + `/auth/unlink` (unificar cuentas federadas).
- [ ] Verificación de email (`email_verified` real).
- [ ] MFA/2FA (TOTP + recuperación): tablas creadas, falta la lógica.
- [ ] Cambio de correo/contraseña y flujo "olvidé contraseña".
- [ ] Alertas de seguridad (hoy solo logs a stdout).
- [ ] El service consulta entidades ORM directamente; la skill `fastapi` §4.2 lo prohíbe → mover al repository.

---

## 6. Reglas del proyecto (baseline)

- Español neutro, sin voseo. Seguridad primero: nada de secretos en BD ni en código.
- No sobreingeniería: solo lo necesario. Evidencia: no afirmar comportamientos sin verificar.
- El usuario ejecuta git commit; el agente solo propone mensajes.

---

## 7. Notas

- Los proyectos originales (`biblioteca-wallmapu-python`, `game_guides_python`) **no fueron modificados**.
- El `client_id` ya no va en la BD: vive en `.env` y debe coincidir con el del frontend.
- Compatible con PostgreSQL.
