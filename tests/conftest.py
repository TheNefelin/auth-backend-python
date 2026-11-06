"""Fixtures de integración: usan TEST_DATABASE_URL (BD dedicada de tests).

- Aplica `schema_auth.sql` (idempotente: CREATE TABLE IF NOT EXISTS + seeds
  con ON CONFLICT) sobre la BD de tests una vez por sesión.
- Cada test corre en una transacción que se **revierte** al final → no deja
  datos, no toca la BD de desarrollo.
- Override de `get_db` para que la app use la BD de test.
- El rate limit se desactiva: los tests no prueban abuso, y compartir la clave
  por IP haría que unos tests agotaran el cupo de otros.
- Google (tokeninfo/userinfo) se mockea en los tests; la BD es real.

Si `TEST_DATABASE_URL` no está definida, los tests de integración se **saltan**
(no fallan) para no romper la suite unitaria.
"""

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.core.config import settings
from src.core.database import get_db
from src.core.limiter import limiter
from src.main import app

# Sin rate limit en tests: la clave es por IP (`test`) y unos tests agotarían
# el cupo de otros, dando 429 en vez del comportamiento bajo prueba.
limiter.enabled = False

SCHEMA_FILE = Path(__file__).resolve().parents[1] / "schema_auth.sql"

requires_test_db = pytest.mark.skipif(
    not settings.TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL no configurada; se omiten los tests de integración",
)


def _split_sql(sql: str) -> list[str]:
    """Divide el .sql en sentencias, ignorando comentarios de línea."""
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


@pytest_asyncio.fixture
async def test_engine():
    """Engine async contra la BD de tests (function-scope para un solo loop).

    Aplica el esquema de forma idempotente (`CREATE TABLE IF NOT EXISTS`).
    """
    from sqlalchemy import text

    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        # utf-8-sig descarta el BOM si el .sql lo trae.
        sql = SCHEMA_FILE.read_text(encoding="utf-8-sig")
        for statement in _split_sql(sql):
            await conn.execute(text(statement))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Sesión en una transacción externa que se revierte al final del test."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient con `get_db` apuntando a la sesión de test (aislada).

    Añade la cabecera `X-API-Key` por defecto: las rutas de sesión
    (`/auth/me`, `/auth/refresh`, `/auth/logout`) la exigen, igual que el BFF.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": settings.API_KEY},
    ) as c:
        yield c
    app.dependency_overrides.clear()
