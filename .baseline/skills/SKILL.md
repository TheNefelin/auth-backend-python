# SKILL.md — backend-python (FastAPI + SQL)

> Guía de referencia para el stack del backend. Leelas antes de tocar código.
> Los skills completos están en `.baseline/skills/`.

## Skills disponibles

| Skill | Ruta | Cuándo usar |
|-------|------|-------------|
| `fastapi` | `.baseline/skills/fastapi/SKILL.md` | Endpoints, modelos ORM, servicios, auth, uploads, email, testing |
| `sql` | `.baseline/skills/sql/SKILL.md` | Esquema, tablas, índices, consultas, transacciones, migraciones |

## Cuándo NO usar

| Situación | Skill |
|-----------|-------|
| Diseño visual / mockups | `ui-ux-mockup` |
| Implementación dotnet | `dotnet` |

## Referencias (se leen bajo demanda)

- `fastapi`: `references/auth.md`, `references/uploads.md`, `references/email.md`, `references/rate-limiting.md`, `references/tests.md`, `references/ejemplo-crud.md`, `references/dtos.md`, `references/modelos.md`, `references/errores-rfc9457.md`, `references/configuracion-logging.md`
- `sql`: `references/postgresql.md`, `references/sqlserver.md`

## Notas

- Este proyecto es el MVP del backend de autenticación transversal.
- El código se implementará desde cero (no se modifica código existente sin autorización).
- El stack es Python + FastAPI + SQLAlchemy 2.1 (async) + PostgreSQL.
- Lee `.baseline/skills/fastapi/SKILL.md` y `.baseline/skills/sql/SKILL.md` para replicar el patrón senior.