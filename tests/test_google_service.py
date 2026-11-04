"""Tests unitarios de api/auth/google_service.py (httpx mockeado, sin red)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.api.auth.google_service import fetch_google_userinfo, verify_google_token
from src.core.config import settings


def _fake_response(status_code: int, json_data: dict | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


def _patch_httpx(response=None, side_effect=None):
    """Devuelve un patch de httpx.AsyncClient cuyo get() responde lo indicado."""
    client = MagicMock()
    if side_effect is not None:
        client.get = AsyncMock(side_effect=side_effect)
    else:
        client.get = AsyncMock(return_value=response)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return patch("src.api.auth.google_service.httpx.AsyncClient", return_value=cm)


class TestVerifyGoogleToken:
    async def test_token_vacio_devuelve_none(self):
        assert await verify_google_token("") is None

    async def test_token_valido_ok(self):
        payload = {
            "sub": "123",
            "email": "a@b.com",
            "email_verified": "true",
            "aud": settings.GOOGLE_CLIENT_ID,
            "iss": "https://accounts.google.com",
        }
        with _patch_httpx(response=_fake_response(200, payload)):
            result = await verify_google_token("access-token-opaco")
        assert result == payload

    async def test_aud_incorrecto_devuelve_none(self):
        payload = {"aud": "otro-client-id", "email_verified": "true"}
        with _patch_httpx(response=_fake_response(200, payload)):
            assert await verify_google_token("token") is None

    async def test_email_no_verificado_devuelve_none(self):
        payload = {"aud": settings.GOOGLE_CLIENT_ID, "email_verified": "false"}
        with _patch_httpx(response=_fake_response(200, payload)):
            assert await verify_google_token("token") is None

    async def test_status_no_200_devuelve_none(self):
        with _patch_httpx(response=_fake_response(400)):
            assert await verify_google_token("token") is None

    async def test_error_de_red_devuelve_none(self):
        with _patch_httpx(side_effect=httpx.ConnectError("sin red")):
            assert await verify_google_token("token") is None


class TestFetchGoogleUserinfo:
    async def test_userinfo_ok(self):
        data = {"given_name": "Ana", "family_name": "Perez", "picture": "http://img"}
        with _patch_httpx(response=_fake_response(200, data)):
            assert await fetch_google_userinfo("token") == data

    async def test_userinfo_falla_devuelve_none(self):
        with _patch_httpx(response=_fake_response(401)):
            assert await fetch_google_userinfo("token") is None

    async def test_userinfo_error_red_devuelve_none(self):
        with _patch_httpx(side_effect=httpx.TimeoutException("timeout")):
            assert await fetch_google_userinfo("token") is None
