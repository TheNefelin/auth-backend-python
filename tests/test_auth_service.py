"""Tests unitarios de AuthService.refresh_token (repos mockeados, sin BD)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.auth.service import AuthService
from src.core.exceptions import UnauthorizedError


def _service() -> AuthService:
    return AuthService(db_session=MagicMock())


def _session(*, revoked=False, expires_in_min=60, last_used_min_ago=0):
    s = MagicMock()
    s.is_revoked = revoked
    s.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_min)
    s.last_used_at = datetime.now(timezone.utc) - timedelta(minutes=last_used_min_ago)
    s.user_id = "user-uuid"
    return s


class TestRefreshToken:
    async def test_sin_sesion_rechaza(self):
        with patch.object(AuthService, "_issue_tokens", new=AsyncMock()):
            with patch("src.api.auth.service.UserSessionRepository") as repo_cls:
                repo_cls.return_value.get_by_refresh_token = AsyncMock(return_value=None)
                with pytest.raises(UnauthorizedError):
                    await _service().refresh_token("token")

    async def test_sesion_revocada_rechaza(self):
        with patch("src.api.auth.service.UserSessionRepository") as repo_cls:
            repo_cls.return_value.get_by_refresh_token = AsyncMock(return_value=_session(revoked=True))
            with pytest.raises(UnauthorizedError):
                await _service().refresh_token("token")

    async def test_expiracion_absoluta_revoca_y_rechaza(self):
        sess = _session(expires_in_min=-1)  # ya expiró
        with patch("src.api.auth.service.UserSessionRepository") as repo_cls:
            repo = repo_cls.return_value
            repo.get_by_refresh_token = AsyncMock(return_value=sess)
            repo.revoke = AsyncMock()
            with pytest.raises(UnauthorizedError):
                await _service().refresh_token("token")
            repo.revoke.assert_awaited_once_with(sess)

    async def test_idle_timeout_revoca_y_rechaza(self):
        sess = _session(last_used_min_ago=9999)  # inactividad enorme
        with patch("src.api.auth.service.UserSessionRepository") as repo_cls:
            repo = repo_cls.return_value
            repo.get_by_refresh_token = AsyncMock(return_value=sess)
            repo.revoke = AsyncMock()
            with pytest.raises(UnauthorizedError):
                await _service().refresh_token("token")
            repo.revoke.assert_awaited_once_with(sess)

    async def test_rotacion_valida_emite_nuevo_par_conservando_techo(self):
        sess = _session()
        new_tokens = {"access_token": "new-a", "refresh_token": "new-r", "expires_in": 900}
        with patch("src.api.auth.service.UserSessionRepository") as repo_cls:
            repo = repo_cls.return_value
            repo.get_by_refresh_token = AsyncMock(return_value=sess)
            repo.revoke = AsyncMock()
            with patch.object(AuthService, "_issue_tokens", new=AsyncMock(return_value=new_tokens)) as issue:
                service = _service()
                service.db.get = AsyncMock(return_value=MagicMock(can_authenticate=lambda: True))
                result = await service.refresh_token("token")

        assert result == new_tokens
        repo.revoke.assert_awaited_once_with(sess)
        # La rotación conserva el techo absoluto de la sesión original.
        assert issue.await_args.kwargs["expires_at"] == sess.expires_at
