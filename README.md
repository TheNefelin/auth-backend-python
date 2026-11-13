# auth-backend-python — Sistema de Autenticación

Backend FastAPI para autenticación transversal (email + contraseña y Google).
Estado actual: **login clásico, registro y Google funcionales**; GitHub y Apple están **pendientes** (aún sin rutas en el backend; el frontend ya tiene los botones stub).

## Relaciones clave
- `users.user_role_id` → `user_roles.id`
- `users.status_id` → `user_status.id`
- `user_identities.user_id` → `users.id` (**ON DELETE RESTRICT**, no CASCADE)
- `user_identities.provider_id` → `auth_providers.id` (**ON DELETE RESTRICT**)
- `user_sessions.user_id` → `users.id` (**ON DELETE RESTRICT**, no CASCADE)

## Modelo de Datos
El esquema se define en `auth-backend-python/schema_auth.sql` (se aplica manualmente a PostgreSQL; no hay migraciones Alembic). Tablas principales:
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
| `POST` | `/auth/login` | Login con email + contraseña, retorna JWT + refresh token |
| `POST` | `/auth/register` | Registro local (email + contraseña), auto-login: retorna JWT + refresh token |
| `POST` | `/auth/refresh` | Renueva JWT usando refresh token (rotación de sesión) |
| `POST` | `/auth/logout` | Revoca las sesiones del usuario (requiere Bearer + X-API-Key) |
| `GET` | `/auth/me` | Perfil del usuario autenticado (requiere Bearer + X-API-Key) |
| `GET` | `/health` | Health check (sin autenticación) |

## Reglas de Seguridad
1. **Nunca confíes solo en el email:** el email de Google puede cambiar. Usa `user_identities.provider_user_id` (sub de Google) como identidad estable.
2. **Valida `aud`:** evita que un access token emitido para otra aplicación se use en la tuya.
3. **Exige `email_verified`:** evita cuentas sin verificar en Google.
4. **Rotación de refresh tokens:** cada uso genera uno nuevo y revoca el anterior. Se guarda solo el **hash SHA-256** (nunca el token en claro).
5. **Expiración absoluta + idle timeout:** la sesión muere a lo sumo en `JWT_REFRESH_EXPIRE_DAYS` y, antes, por inactividad (`JWT_REFRESH_IDLE_MINUTES`).
6. **Rol por request:** `require_user` / `require_admin` leen el rol real de la BD, no del token.
7. **API Key (X-API-Key):** todas las rutas de `/auth/*` exigen la cabecera `X-API-Key` (solo el BFF la conoce). `/health` y `/docs` quedan fuera (infraestructura).
8. **Comparación en tiempo constante:** `secrets.compare_digest` para la API Key (evita timing attacks).

## Instalación

```bash
# 1. Clonar repositorio
git clone <url-del-repositorio>
cd auth-backend-python

# 2. Crear entorno virtual
py -m venv .venv

# 3. Activar el entorno virtual (SIEMPRE antes de instalar/correr/testear)
#    Windows PowerShell:  .venv\Scripts\activate
#    Windows CMD:         .venv\Scripts\activate.bat
#    Linux/Mac:           source .venv/bin/activate
#    Al activarlo, el prompt debe mostrar (.venv)

# 4. Instalar paquetes del backend (con el venv activo)
```

### 4.1 Core / API (FastAPI + Uvicorn + Pydantic)
```bash
pip install fastapi uvicorn pydantic
```

### 4.2 Base de datos (SQLAlchemy + asyncpg + dotenv)
```bash
pip install sqlalchemy asyncpg python-dotenv
```

### 4.3 Seguridad (JWT + passwords)
```bash
pip install python-jose[cryptography] pwdlib[bcrypt] bcrypt
```

### 4.4 HTTP / integración externa (Google)
```bash
pip install httpx
```

### 4.5 Control de errores (RFC 9457)
```bash
pip install fastapi-problem rfc9457
```

### 4.6 Rate limiting
```bash
pip install slowapi
```

### 4.7 Testing (solo desarrollo)
```bash
pip install pytest pytest-asyncio
```

### 4.8 Guarda e Instala dependencias
```sh
pip freeze > requirements.txt
```
```sh
pip install -r requirements.txt
```

```bash
# 5. Configurar variables de entorno
cp .env.demo .env
# Editar .env con tus credenciales (GOOGLE_CLIENT_ID, JWT_SECRET_KEY, API_KEY, etc.)

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
pytest                       # toda la suite (50 tests)
pytest tests/test_auth_integration.py -v   # un solo archivo
```
Los tests incluyen unitarios + integración con BD real de test (`db_testing`, rollback por test).

## Seguridad
- Las credenciales nunca se commitean al repositorio (`.env` está fuera de git; usa `.env.demo` como plantilla).
- El `JWT_SECRET_KEY` debe ser real y distinto en producción.
- Las refresh tokens se rotan en cada uso y se guardan hasheadas.
- Las revocaciones de sesión deben ser inmediatas al logout.
- La API Key (`API_KEY`) debe coincidir entre frontend (`.env`) y backend (`.env`).

## Pendientes
- GitHub y Apple (replicar el patrón de Google; aún sin rutas en el backend).
- `/auth/connect` (unificar cuentas federadas) y verificación de email.
- MFA/2FA, cambio de correo/contraseña, flujo "olvidé contraseña".
- Alertas de seguridad (hoy solo logs a stdout).
- Mover al repository las queries que hoy hace el service (`select(UserIdentity)`, `db.get(User)`): la skill `fastapi` §4.2 lo prohíbe.

> Nota: la protección contra fuerza bruta ya está cubierta por el rate limit por identidad (`slowapi`) aplicado en `/auth/login` y `/auth/register`.