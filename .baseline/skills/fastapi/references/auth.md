## 8. Auth transversal (OAuth + JWT + Refresh Rotation)

Siempre presente en cualquier API: se reutiliza en todos los proyectos. Componentes:

### 8.0 Hashing de contraseñas — usar `pwdlib`, NO `passlib`

> **⚠️ `passlib` está sin mantenimiento (último release 2020) y está ROTO con `bcrypt` ≥ 4.1** (intenta leer `bcrypt.__about__`, eliminado en bcrypt 4.1+, y falla con `ValueError`/`MissingBackendError` incluso con contraseñas cortas). El reemplazo oficial y mantenido —y el que usa la documentación actual de FastAPI— es **`pwdlib`**.

```python
# src/core/security.py
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

# bcrypt explícito; para argon2id: PasswordHash.recommended() + pwdlib[argon2]
pwd_context = PasswordHash((BcryptHasher(),))

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- **Dependencia:** `pwdlib[bcrypt]` + `bcrypt` (o `pwdlib[argon2]` si se prefiere argon2id).
- `pwdlib` soporta **rotación de algoritmo** (`verify_and_update`): útil para migrar hashes viejos sin forzar re-login.
- Cambiar de `passlib` a `pwdlib` **invalida los hashes viejos**; solo migrar con lógica de rehash o si aún no hay usuarios con password.

### 8.0.1 Roles: el enum es el CONTRATO, la BD es el catálogo

Un error común es tener roles en la BD que el código no "conoce" (o al revés): si alguien cambia `'admin'` → `'Admins'` en `user_roles`, el `require_admin` del código deja de pasar y **todos los admins quedan fuera en silencio**.

Dos mitigaciones (usar según criticidad):
1. **Enum en código como contrato** (`core/roles.py`): `class UserRole(str, Enum): ADMIN = "admin"; USER = "user"`. El código nunca usa strings mágicos (`"admin"`), y el seed del DDL usa **los mismos valores**.
2. **Validación al arranque (recomendada)**: comprobar que los roles del enum existan en `user_roles`; si no, **abortar el arranque** (`lifespan`) en vez de fallar silenciosamente. Convierte un fallo silencioso (usuario no entra, nadie sabe por qué) en uno ruidoso y claro.

> **Cuándo migrar a permisos (patrón escalable):** si los roles deben crearse **sin deploy** (dinámicos), separar **roles (datos, tabla)** de **permisos (código, enum)** con una tabla `role_permissions`: el código pregunta `user.can("users.delete")`, nunca `role == "admin"`. Es más complejo; solo vale si de verdad hay roles dinámicos, no para un `admin`/`user` fijo.

### 8.1 `src/core/security.py` — JWT identifica, el rol se lee de la BD

**Punto clave**: el rol embebido en el token es una *pista*, no una autoridad. En cada request protegido se lee el rol real del usuario desde la BD (`users_service.get_role_name_by_id`): un cambio de rol, una baja de usuario o un refresh de permisos se refleja al instante, sin esperar que expire el token (2h).

```python
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.users import service as users_service
from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import ForbiddenError, UnauthorizedError

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: UUID, role: str) -> str:
  now = datetime.now(tz=timezone.utc)
  payload = {
    "sub": str(user_id),
    "role": role,
    "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    "iat": now,
  }
  return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
  try:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
  except JWTError:
    raise UnauthorizedError()


def get_current_user(required_roles: Optional[list[str]] = None):
  async def _get_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
  ):
    if credentials is None:
      raise UnauthorizedError()

    payload = verify_token(credentials.credentials)

    try:
      user_id = UUID(payload["sub"])
    except (ValueError, KeyError, TypeError):
      raise UnauthorizedError()

    # El rol REAL se lee de la BD, no se confía en el rol del token.
    role = await users_service.get_role_name_by_id(db, user_id)
    if role is None:
      raise UnauthorizedError(message="User no longer exists")

    if required_roles is not None and role not in required_roles:
      raise ForbiddenError()

    payload["role"] = role
    return payload
  return _get_user
```

### 8.2 `src/core/security.py` — Auth + API Key (BFF → API)

**`verify_api_key`** vive en `security.py` (es seguridad, no una "dependency transversal"). Se aplica a **nivel de router** para que ninguna ruta nueva quede sin proteger:

```python
# routes.py
from src.core.security import verify_api_key

api_key_required = Depends(verify_api_key)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(verify_api_key)],  # toda la API exige la Key
)
```

- **Comparación en tiempo constante**: `secrets.compare_digest(x_api_key, settings.API_KEY)` (evita timing attacks).
- **Cabecera opcional en la firma**: `Header(None, alias="X-API-Key")` para que el fallo lo decida la función (401 `invalid-api-key`), no la validación de FastAPI (422, que además expone el nombre del header en el schema público).
- **`API_KEY` es requerida**: `API_KEY: str = _required("API_KEY")` — el arranque falla si falta (un default vacío permitiría que una clave vacía pasara).
- **Rutas públicas por diseño**: `/health`, `/docs`, `/openapi.json` quedan fuera del router de auth. Si se necesitan endpoints públicos dentro de `/auth` (ej. login), se sacan a un sub-router separado.
- **Logging de seguridad**: `logger.warning("API Key inválida recibida")` en cada intento fallido.

### 8.2.1 Logging de eventos de seguridad

Loguear los eventos críticos para detectar ataques:

```python
# service.py
logger.warning("Login fallido: usuario no encontrado o inactivo — email=%s", credentials.email)
logger.warning("Login fallido: contraseña incorrecta — email=%s", credentials.email)
logger.warning("Google login fallido: token inválido")
logger.warning("Reuso de refresh token detectado — user_id=%s, sesiones revocadas", session.user_id)
logger.warning("Reuso concurrente de refresh token — user_id=%s", session.user_id)
```

- Usar `logger = logging.getLogger("auth-unificado")` (o el nombre del proyecto).
- `LOG_LEVEL` configurable por `.env` (default `INFO`).
- No silenciar en producción (a diferencia del frontend, que puede silenciar en dev).

### 8.3 Flujo de login (Google OAuth) en `src/api/auth/`

El `users.service.get_or_create_user` recibe identidad primaria (`google_sub`) y email. `verify_google_token` valida contra Google **aud == GOOGLE_CLIENT_ID** (sin ese check, cualquier token de otra app de Google da acceso).

```python
# routes.py — router con dependencies=[Depends(verify_api_key)]
@router.post("/google", response_model=schemas.AuthGoogleResponse, status_code=HTTP_200_OK)
@limiter.limit("10/minute")  # siempre rate-limit el login
async def auth_google(request: Request, auth_data: schemas.AuthGoogleRequest, db: AsyncSession = Depends(database.get_db)):
  return await service.auth_service(db, auth_data.googleToken)
```

```python
# google_service.py — cliente OAuth (httpx async, sin SDK del proveedor)
async def verify_google_token(access_token: str) -> schemas.GoogleUserInfo:
  async with httpx.AsyncClient(timeout=10) as client:
    response = await client.get(
      GOOGLE_TOKEN_INFO_URL,
      params={"access_token": access_token},
    )
  if response.status_code != 200:
    raise UnauthorizedError(message="Invalid Google token")

  token_info = response.json()
  if settings.GOOGLE_CLIENT_ID and token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
    raise UnauthorizedError(message="Invalid Google token")

  email_verified = token_info.get("email_verified")
  if email_verified not in (True, "true"):
    raise UnauthorizedError(message="Email not verified")

  # /tokeninfo con un access token no garantiza name/picture: si faltan, se
  # consulta /userinfo (misma validez: el token ya fue validado por aud).
  return schemas.GoogleUserInfo(google_id=token_info["sub"], email=token_info["email"], ...)
```

```python
# service.py — orquesta el flujo completo
async def auth_service(db: AsyncSession, google_token: str) -> schemas.AuthGoogleResponse:
  info = await google_service.verify_google_token(google_token)

  user = await users_service.get_or_create_user(db, info.email, info.google_id)

  token = security.create_access_token(user.id, user.role.name)
  refresh_token = secrets.token_urlsafe(32)
  expires_at = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
  # Guardar SOLO el hash: si la BD se filtra, los refresh tokens no son usables.
  await session_repository.create(db, user.id, hash_token(refresh_token), expires_at)

  return schemas.AuthGoogleResponse(token=token, refresh_token=refresh_token, user=...)
```

```python
# users/service.py — get_or_create_user (identidad primaria por google_sub)
async def get_or_create_user(db: AsyncSession, email: str, google_id: str) -> dtos.UserResponse:
  entity = await repository.get_by_google_sub(db, google_id)
  if not entity:
    entity = await repository.get_by_email(db, email)

  if not entity:
    role = await roles_service.get_by_name(db, DEFAULT_ROLE_NAME)  # "user"
    if not role:
      raise NotFoundError("Role")  # el rol por defecto se resuelve por nombre, no con ID en duro
    entity = await repository.create(db, {"email": email, "role_id": role.id, "google_sub": google_id})
  return dtos.UserResponse.model_validate(entity)
```

```python
# refresh rotation: el refresh viejo se revoca y se emite uno nuevo
async def refresh_session(db, refresh_token):
  # Buscar por hash (nunca se guarda el token en claro).
  session = await session_repository.get_by_token_hash(db, hash_token(refresh_token))
  if not session or session.expires_at < datetime.now(tz=timezone.utc):
    raise UnauthorizedError("Invalid or expired refresh token")
  user_id, role_name = session.user_id, session.user.role.name
  # Rotación ATÓMICA: revocar de forma condicional (UPDATE ... SET revoked=true WHERE id=:id AND revoked=false).
  # Si no afecta filas, el token ya se usó → dos refresh concurrentes no emiten dos pares válidos.
  if not await session_repository.revoke_if_active(db, session.id):
    raise UnauthorizedError("Invalid or expired refresh token")
  new_refresh = secrets.token_urlsafe(32)
  await session_repository.create(db, user_id, hash_token(new_refresh), datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS))
  return schemas.AuthRefreshResponse(token=security.create_access_token(user_id, role_name), refresh_token=new_refresh)
```

> **Refresh token — decisión explícita de seguridad y concurrencia**:
> - **Almacenar el hash** (`sha256(token)`), nunca el token en claro; declarar `UNIQUE` sobre esa columna.
> - **Rotación de un solo uso y atómica**: la revocación debe ser condicional (`UPDATE … WHERE revoked = false`); si afecta 0 filas, rechazar.
> - **Detección de reuso**: si llega un token ya revocado, revocar toda la familia de sesiones del usuario (posible robo). *Trade-off conocido*: un atacante con tokens viejos podría forzar logout del usuario legítimo (DoS); se acepta porque prioriza la protección contra robo (patrón Auth0).
> - **Expiración absoluta + idle timeout (recomendado)**: la sesión caduca como máximo en `expires_at` (fijo desde el login) **y además** por inactividad, con una columna `last_used_at` que se actualiza en cada uso. Sin idle timeout, un refresh robado puede permanecer válido todo el techo absoluto aunque el usuario real ya no use la app.
>
>   ```python
>   now = datetime.now(tz=timezone.utc)
>   if session.expires_at <= now:
>     await session_repository.revoke(db, session)          # techo absoluto
>     raise UnauthorizedError("Refresh token has expired")
>   if session.last_used_at <= now - timedelta(minutes=REFRESH_IDLE_MINUTES):
>     await session_repository.revoke(db, session)          # inactividad
>     raise UnauthorizedError("Session expired due to inactivity")
>   if not await session_repository.revoke_if_active(db, session.id):  # reuso concurrente
>     await session_repository.revoke_all_for_user(db, session.user_id)
>     raise UnauthorizedError("Refresh token reuse detected; sessions revoked")
>   ```
>   El `expires_at` de la rotación **conserva** el techo absoluto original (no se extiende en cada refresh); solo el login fija uno nuevo.

### 8.4 Endpoints de usuario autenticado

El `user_id` **nunca viene del body**: se extrae del token.

```python
# src/api/user_favorites/routes.py (ejemplo transversal de feature "del usuario")
from uuid import UUID
from fastapi import APIRouter, Depends

from src.core.dependencies import verify_api_key, require_user

router = APIRouter(prefix="/user-favorites", tags=["user-favorites"], dependencies=[Depends(verify_api_key)])


def get_user_id(payload: dict = Depends(require_user)) -> UUID:
  return UUID(payload["sub"])


@router.post("/", response_model=dtos.UserFavoriteResponse, status_code=201)
async def add_to_favorites(data: dtos.UserFavoriteRequest, user_id: UUID = Depends(get_user_id), db=Depends(get_db)):
  return await service.create(db, user_id, data.product_id)
```

**Regla de dependencia**: la dependency `get_user_id` es del feature (rutas del feature), **no** de `core/dependencies.py` — la reutilización del feature evita que `core/` se acople a dominios.

Patrón `upsert` en el repository (no falla por PK duplicada): si la fila existe se actualiza, si no se crea.

**Features `roles`**: catálogo de roles sin routes (solo `repository.py` + `service.py`). Lo consumen `users` y `security` (resolución de rol por nombre y de nombre de rol del usuario). El `"role"` default se resuelve por **nombre** (`service.get_by_name(db, "user")`), nunca con ID en duro.
