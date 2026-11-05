"""Tests unitarios de la autorización por rol (core/dependencies.py)."""

import pytest

from src.core.dependencies import require_admin, require_user
from src.core.exceptions import ForbiddenError


def _user(role: str) -> dict:
    return {"id": "u-1", "email": "a@b.com", "name": "X", "role": role, "is_active": True}


class TestRequireUser:
    @pytest.mark.parametrize("role", ["user", "admin"])
    async def test_roles_permitidos(self, role):
        assert await require_user(_user(role)) == _user(role)

    @pytest.mark.parametrize("role", ["guest", "invitado", ""])
    async def test_roles_denegados(self, role):
        with pytest.raises(ForbiddenError) as exc:
            await require_user(_user(role))
        assert exc.value.status == 403


class TestRequireAdmin:
    async def test_admin_permitido(self):
        assert await require_admin(_user("admin")) == _user("admin")

    @pytest.mark.parametrize("role", ["user", "guest", ""])
    async def test_no_admin_denegado(self, role):
        with pytest.raises(ForbiddenError) as exc:
            await require_admin(_user(role))
        assert exc.value.status == 403
