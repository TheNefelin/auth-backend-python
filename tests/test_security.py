"""Tests unitarios de core/security.py (sin BD)."""

from datetime import timedelta

import pytest

from src.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_y_verify_ok(self):
        hashed = get_password_hash("Secreta123")
        assert hashed != "Secreta123"
        assert verify_password("Secreta123", hashed) is True

    def test_verify_password_incorrecta(self):
        hashed = get_password_hash("Secreta123")
        assert verify_password("OtraClave", hashed) is False


class TestAccessToken:
    def test_token_roundtrip(self):
        token = create_access_token(subject="user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert "exp" in payload and "iat" in payload

    def test_token_expirado_lanza_valueerror(self):
        token = create_access_token(subject="user-123", expires_delta=timedelta(seconds=-1))
        with pytest.raises(ValueError):
            decode_access_token(token)

    def test_token_malformado_lanza_valueerror(self):
        with pytest.raises(ValueError):
            decode_access_token("esto-no-es-un-jwt")


class TestRefreshToken:
    def test_genera_tokens_distintos(self):
        assert generate_refresh_token() != generate_refresh_token()

    def test_hash_es_estable_y_no_reversible(self):
        token = generate_refresh_token()
        h1 = hash_refresh_token(token)
        h2 = hash_refresh_token(token)
        assert h1 == h2
        assert h1 != token
        assert len(h1) == 64  # SHA-256 hex

    def test_hashes_distintos_para_tokens_distintos(self):
        assert hash_refresh_token(generate_refresh_token()) != hash_refresh_token(generate_refresh_token())
