# backend-python — Sistema de Autenticación

Backend FastAPI para autenticación transversal. Estado actual: **login con Google funcional**; email+contraseña, GitHub y Apple están **pendientes**.

## Relaciones clave
- `users.user_role_id` → `user_roles.id`
- `users.status_id` → `user_status.id`
- `user_identities.user_id` → `users.id` (**ON DELETE RESTRICT**, no CASCADE)
- `user_identities.provider_id` → `auth_providers.id` (**ON DELETE RESTRICT**)
- `user_sessions.user_id` → `users.id` (**ON DELETE RESTRICT**, no CASCADE)

## Modelo de Datos
El esquema se define en `backend-python/schema_auth.sql` (se aplica manualmente a PostgreSQL; no hay migraciones Alembic). Tablas principales:
- `users`: perfil principal con soft delete (`deleted_at`)
- `user_identities`: vínculos federados (Google, GitHub, Apple, local)
- `user_sessions`: sesiones activas mediante refresh tokens
- `auth_providers`: catálogo de proveedores (`local`, `google`, `github`, `apple`)
- `user_roles`, `user_status`: catálogos de roles y estados

## Configuración de Proveedores
Los `client_id` y URLs de los proveedores **no se guardan en la BD**: se gestionan en `.env`.

| Variable | Valor ejemplo |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | `123456789.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | (dejar vacío) |
| `GITHUB_CLIENT_ID` | `123456789` |
| `GITHUB_CLIENT_SECRET` | (dejar vacío) |
| `APPLE_CLIENT_ID` | `1234567890.com.example.app` |
| `APPLE_CLIENT_SECRET` | (dejar vacío) |
| `GOOGLE_TOKEN_INFO_URL` | `https://oauth2.googleapis.com/tokeninfo` |
| `GOOGLE_USERINFO_URL` | `https://www.googleapis.com/oauth2/v3/userinfo` |
| `GOOGLE_ISSUER` | `https://accounts.google.com` |
| `GOOGLE_SCOPE` | `openid email profile` |

## Configuración JWT
| Variable | Descripción | Valor ejemplo |
|----------|-------------|-------------|
| `JWT_SECRET_KEY` | Secreto para firmar JWTs (HS256). **Requerido** | `cambiar_en_produccion` |
| `JWT_ALGORITHM` | Algoritmo de firma | `HS256` |
| `JWT_ACCESS_EXPIRE_MINUTES` | Vida del JWT de acceso | `15` |
| `JWT_REFRESH_EXPIRE_DAYS` | Vida absoluta del refresh token | `1` |
| `JWT_REFRESH_IDLE_MINUTES` | Timeout de inactividad del refresh | `30` |

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/google` | Login con Google (valida token OAuth 2.0), retorna JWT + refresh token |
| `POST` | `/auth/login` | Login con email + contraseña (pendiente de implementación) |
| `POST` | `/auth/register` | Registro (pendiente de implementación) |
| `POST` | `/auth/refresh` | Renueva JWT usando refresh token (rotación de sesión) |
| `POST` | `/auth/logout` | Revoca las sesiones del usuario (requiere Bearer) |
| `GET` | `/auth/me` | Perfil del usuario autenticado (requiere Bearer) |

## Reglas de Seguridad
1. **Nunca confíes solo en el email:** el email de Google puede cambiar. Usa `user_identities.provider_user_id` (sub de Google) como identidad estable.
2. **Valida `aud`:** evita que un access token emitido para otra aplicación se use en la tuya.
3. **Exige `email_verified`:** evita cuentas sin verificar en Google.
4. **Rotación de refresh tokens:** cada uso genera uno nuevo y revoca el anterior. Se guarda solo el **hash SHA-256** (nunca el token en claro).
5. **Expiración absoluta + idle timeout:** la sesión muere a lo sumo en `JWT_REFRESH_EXPIRE_DAYS` y, antes, por inactividad (`JWT_REFRESH_IDLE_MINUTES`).
6. **Rol por request:** `require_user` / `require_admin` leen el rol real de la BD, no del token.

## Instalación
```bash
# 1. Clonar repositorio
git clone <url-del-repositorio>
cd backend-python

# 2. Crear entorno virtual
py -m venv .venv

# 3. Activar el entorno virtual (SIEMPRE antes de instalar/correr/testear)
#    Windows PowerShell:  .venv\Scripts\activate
#    Windows CMD:         .venv\Scripts\activate.bat
#    Linux/Mac:           source .venv/bin/activate
#    Al activarlo, el prompt debe mostrar (.venv)

# 4. Instalar paquetes del backend (con el venv activo)
pip install fastapi uvicorn sqlalchemy pwdlib[bcrypt] bcrypt python-jose[cryptography] pydantic python-dotenv httpx

# 4.1 Instalar dependencias de testing (solo desarrollo)
pip install pytest pytest-asyncio

# 5. Configurar variables de entorno
cp .env.demo .env
# Editar .env con tus credenciales (GOOGLE_CLIENT_ID, JWT_SECRET_KEY, etc.)

# 6. Crear la base de datos y aplicar el esquema
createdb auth_db
psql -d auth_db -f schema_auth.sql

# 7. Ejecutar el servidor (con el venv activo)
python run.py
```

> **Regla del entorno:** todo (instalar, correr, testear) se hace **con el venv activo**.
> El prompt debe mostrar `(.venv)`. No mezcles `py` (Python global) con el venv:
> el venv está aislado (`include-system-site-packages = false`) y no ve el global.

## Tests
```bash
# Con el venv activo
pytest                       # toda la suite
pytest tests/test_security.py -v   # un solo archivo
```
Los tests son **unitarios** (no tocan base de datos): mockean repositories y servicios externos.

## Seguridad
- Las credenciales nunca se commitean al repositorio (`.env` está fuera de git; usa `.env.demo` como plantilla).
- El `JWT_SECRET_KEY` debe ser real y distinto en producción.
- Las refresh tokens se rotan en cada uso y se guardan hasheadas.
- Las revocaciones de sesión deben ser inmediatas al logout.

## Pendientes
- Login email+contraseña y `/auth/register` (la lógica existe parcialmente; falta verificación de password con `pwdlib`).
- GitHub y Apple (stubs; replicar el patrón de Google).
- API Key global (`X-API-Key`) — **no implementada**.
- Detección de reuso del refresh token (revocar la familia de sesiones).
