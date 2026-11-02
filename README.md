# backend-python - Sistema de Autenticación
## Relaciones clave
- `users.user_role_id` → `user_roles.id`
- `users.status_id` → `user_status.id`
- `user_identities.user_id` → `users.id` (**ON DELETE RESTRICT**, no CASCADE)
- `user_identities.provider_id` → `auth_providers.id` (**ON DELETE RESTRICT**)
- `user_sessions.user_id` → `users.id` (**ON DELETE RESTRICT**, no CASCADE)

## Configuración de Proveedores
Los `client_id` y URLs de los proveedores **no se guardan en la BD**. Se gestionan exclusivamente en las variables de entorno `.env`:

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

## TOKEN_SECRET_KEY y configuración JWT
| Variable | Descripción | Valor ejemplo |
|----------|-------------|-------------|
| `TOKEN_SECRET_KEY` | Secreto para firmar JWTs (HS256) | `cambiar_en_produccion` |
| `JWT_ALGORITHM` | Algoritmo de firma | `HS256` |
| `TOKEN_ACCESS_EXPIRE_MINUTES` | Vida del JWT de acceso | `15` |
| `TOKEN_REFRESH_EXPIRE_DAYS` | Vida del refresh token | `7` |

## Descripción
Backend FastAPI para el sistema de autenticación transversal. Gestiona login con email + contraseña, Google, GitHub y Apple, refresh tokens, y vinculación de proveedores.

## Modelo de Datos
El esquema de base de datos se encuentra en `schema_auth.sql` (raíz del workspace). Tablas principales:
- `users`: Perfil principal con soft delete (`deleted_at`)
- `user_identidades`: Vinculos federados (Google, GitHub, Apple, local)
- `user_sessions`: Sesiones activas mediante refresh tokens
- `auth_providers`: Catálogo de proveedores (`local`, `google`, `github`, `apple`)
- `user_roles`, `user_status`: Catálogos de roles y estados
## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/login` | Login con email + contrasena, retorna JWT + refresh token |
| `POST` | `/auth/google` | Login con Google, valida token OAuth 2.0, retorna JWT + refresh token |
| `POST` | `/auth/refresh` | Renueva JWT usando refresh token (rotación de sesión) |
| `POST` | `/auth/logout` | Revoca refresh token (cierra sesión) |
| `POST` | `/auth/connect` | Vincula un proveedor externo a la cuenta autenticada |
| `DELETE` | `/auth/unlink/{provider}` | Desvincula un proveedor de la cuenta autenticada |

## Reglas de Seguridad
1. **Nunca confies solo en el email:** el email de Google puede cambiar. Usa `user_identities.provider_user_id` (sub de Google) como identidad estable.
2. **Valida `aud`:** evita que un access token emitido para otra aplicación se use en la tuya.
3. **Exige `email_verified`:** evita cuentas sin verificar en Google.
4. **Rotación de refresh tokens:** cada uso genera uno nuevo y revoca el anterior.
5. **Rol obligatorio:** un usuario sin rol no puede obtener JWT.
6. **No hay merge automático por email:** vincular una cuenta federada a una existente requiere acción explícita y autenticada.

## Instalación
```bash
# 1. Clonar repositorio
git clone <url-del-repositorio>
cd backend-python

# 2. Crear entorno virtual
py -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar paquetes del backend
pip install fastapi uvicorn sqlalchemy passlib[jbcrypt] python-jose[cryptography] pydantic alembic python-dotenv httpx

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales (GOOGLE_CLIENT_ID, TOKEN_SECRET_KEY, etc.)

# 5. Instalar dependencias del proyecto raíz (opcional, para usar utilidades)
cd ..
pip install -e auth_google_unificado  # o instalar el proyecto en modo desarrollo

# 6. Inicializar base de datos
cd auth_google_unificado
# Crear base de datos PostgreSQL
createdb auth_db
# Aplicar migraciones desde schema_auth.sql
pip install alembic
alembic upgrade head

# 7. Ejecutar el servidor
uvicorn src.main:app --reload
```

## API Key Management
- El `API_KEY` se usa en el header `X-API-Key` en todas las peticiones HTTP
- El interceptor global en el frontend lo agrega automáticamente
- Nunca commits `.env` a repositorios públicos

## Migración desde prototipo (`prototype_python/`)
Notable cambio en esta versión:
- `client_id` ya no en `schema_auth.sql`, sino en `.env`
- Nuevas características: MFA/2FA (posteriormente), brute-force protection
- Estructura de features separadas: `auth`, `users`, `user_identities`, `user_sessions`
- Endpoints: `/auth/connect` (antes `/auth/link`), `/auth/unlink/{provider}`
- Migración de BD: `schema_auth.sql` ahora tiene tablas MFA añadidas

## Seguridad
- Las credenciales nunca se deben commitear al repositorio
- Usar `python-dotenv` para cargar variables de entorno
- El `TOKEN_SECRET_KEY` debe ser cambiado en producción
- Las refresh tokens deben rotarse en cada uso
- Las revocaciones de sesión deben ser inmediatas al logout
```
`,
 success
</think>

El contenido se insertó. Ahora voy a verificar el estado y luego generar el mensaje final de commit.

## 📊 Verificando el archivo

Vamos a verificar que el archivo tenga el contenido esperado.

## 📖 Leyendo el `backend-python/README.md`

Vamos a leer el archivo para ver su estado final:</think>
<tool_call>
<function=read_files>
<parameter=files>
["D:/Repo/FullStack/auth_google_unificado/backend-python/README.md"]
