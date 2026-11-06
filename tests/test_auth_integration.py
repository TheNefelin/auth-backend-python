"""Tests de integración de auth (BD real de test + Google mockeado).

Requieren TEST_DATABASE_URL. Cada test se revierte al terminar (ver conftest).
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text

from src.core.config import settings
from tests.conftest import requires_test_db

pytestmark = requires_test_db


def _google_info(email="user@example.com", sub="google-sub-1"):
    return {
        "sub": sub,
        "email": email,
        "email_verified": True,
        "aud": settings.GOOGLE_CLIENT_ID,
        "iss": "https://accounts.google.com",
        "given_name": "Demo",
        "family_name": "User",
    }


# ---------------------------------------------------------------- register

async def test_register_ok_devuelve_tokens(client, db_session):
    r = await client.post("/auth/register", json={"email": "nuevo@example.com", "password": "Secreta123"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]

    # Identidad local creada
    row = (await db_session.execute(text(
        "SELECT p.name FROM user_identities i "
        "JOIN auth_providers p ON p.id = i.provider_id "
        "WHERE i.email = :e"
    ), {"e": "nuevo@example.com"})).fetchall()
    assert ("local",) in row


async def test_register_email_duplicado_409(client):
    payload = {"email": "dup@example.com", "password": "Secreta123"}
    assert (await client.post("/auth/register", json=payload)).status_code == 200
    assert (await client.post("/auth/register", json=payload)).status_code == 409


async def test_register_password_corta_422(client):
    r = await client.post("/auth/register", json={"email": "x@example.com", "password": "123"})
    assert r.status_code == 422


async def test_register_email_invalido_422(client):
    r = await client.post("/auth/register", json={"email": "sin-arroba", "password": "Secreta123"})
    assert r.status_code == 422


# ---------------------------------------------------------------- login

async def test_login_ok(client):
    await client.post("/auth/register", json={"email": "login@example.com", "password": "Secreta123"})
    r = await client.post("/auth/login", json={"email": "login@example.com", "password": "Secreta123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


async def test_login_password_mala_401(client):
    await client.post("/auth/register", json={"email": "login2@example.com", "password": "Secreta123"})
    r = await client.post("/auth/login", json={"email": "login2@example.com", "password": "MalaClave"})
    assert r.status_code == 401


async def test_login_email_inexistente_401(client):
    r = await client.post("/auth/login", json={"email": "nadie@example.com", "password": "Secreta123"})
    assert r.status_code == 401


# ---------------------------------------------------------------- google (mockeado)

async def test_google_login_ok(client, db_session):
    with patch("src.api.auth.google_service.verify_google_token", new=AsyncMock(return_value=_google_info())), \
         patch("src.api.auth.google_service.fetch_google_userinfo", new=AsyncMock(return_value={"given_name": "Demo", "family_name": "User"})):
        r = await client.post("/auth/google", json={"googleToken": "cualquiera"})
    assert r.status_code == 200
    assert r.json()["access_token"]


async def test_google_login_token_invalido_401(client):
    with patch("src.api.auth.google_service.verify_google_token", new=AsyncMock(return_value=None)):
        r = await client.post("/auth/google", json={"googleToken": "malo"})
    assert r.status_code == 401


# ---------------------------------------------------------------- me

async def test_me_sin_token_401(client):
    assert (await client.get("/auth/me")).status_code == 401


async def test_me_con_token_ok(client):
    reg = await client.post("/auth/register", json={"email": "me@example.com", "password": "Secreta123"})
    token = reg.json()["access_token"]
    r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"
    assert r.json()["provider"] == "local"


# ---------------------------------------------------------------- refresh

async def test_refresh_ok_rota(client):
    reg = await client.post("/auth/register", json={"email": "ref@example.com", "password": "Secreta123"})
    refresh = reg.json()["refresh_token"]
    r = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert r.json()["refresh_token"] != refresh


async def test_refresh_reuso_401_y_revoca(client):
    reg = await client.post("/auth/register", json={"email": "reuse@example.com", "password": "Secreta123"})
    refresh = reg.json()["refresh_token"]

    # Primer uso: rota
    assert (await client.post("/auth/refresh", json={"refresh_token": refresh})).status_code == 200
    # Segundo uso del mismo (ya revocado) → reuso
    assert (await client.post("/auth/refresh", json={"refresh_token": refresh})).status_code == 401


# ---------------------------------------------------------------- logout

async def test_logout_revoca_sesion(client):
    reg = await client.post("/auth/register", json={"email": "out@example.com", "password": "Secreta123"})
    token = reg.json()["access_token"]
    r = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
