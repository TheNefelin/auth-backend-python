"""Validaciones de arranque de la aplicación.

Estrategia de roles (contrato enum ↔ BD): el enum `UserRole` y la tabla
`user_roles` pueden divergir si alguien edita la BD. Esta comprobación
**aborta el arranque** si falta un rol del enum en la tabla, evitando el
fallo silencioso (usuarios que dejan de pasar `require_user`/`require_admin`).
"""

import logging

from sqlalchemy import select

from .database import AsyncSessionLocal
from .roles import UserRole
from ..models import UserRole as UserRoleModel

logger = logging.getLogger(__name__)


async def assert_roles_consistent() -> None:
    """Verifica que todos los roles del enum existan en la tabla `user_roles`."""
    async with AsyncSessionLocal() as session:
        rows = await session.execute(select(UserRoleModel.name))
        db_roles = {name for (name,) in rows.all()}

    missing = [role.value for role in UserRole if role.value not in db_roles]
    if missing:
        raise RuntimeError(
            "Roles del código ausentes en la tabla 'user_roles': "
            f"{missing}. El enum `UserRole` y el seed de la BD deben coincidir."
        )

    logger.info("Roles consistentes: %s", sorted(db_roles))
