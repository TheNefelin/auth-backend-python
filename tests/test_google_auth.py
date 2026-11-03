"""Basic tests for Google authentication functionality."""

import pytest
from unittest.mock import AsyncMock, patch

# Test the Google service module functions
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.auth.google_service import verify_google_token, verify_id_token
class TestGoogleAuthService:
    """Test suite for Google authentication services."""

    @pytest.mark.asyncio
    async def test_verify_id_token_valid(self):
        """Test successful id_token validation."""
        mock_payload = {
            "sub": "test_user_123",
            "email": "test@example.com",
            "email_verified": True,
            "iss": "accounts.google.com",
            "aud": "test_client_id"
        }

        with patch("src.api.auth.google_service.jwt.decode") as mock_decode:
            mock_decode.return_value = mock_payload

            result = await verify_id_token("mock.jwt.token.here")

            assert result == mock_payload
            mock_decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_id_token_invalid_issuer(self):
        """Test id_token validation with invalid issuer."""
        mock_payload = {
            "sub": "test_user_123",
            "email": "test@example.com",
            "email_verified": True,
            "iss": "invalid_issuer",
            "aud": "test_client_id"
        }

        with patch("src.api.auth.google_service.jwt.decode") as mock_decode:
            mock_decode.return_value = mock_payload

            result = await verify_id_token("mock.jwt.token.here")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_google_token_id_token(self):
        """Test id_token validation through main function."""
        with patch("src.api.auth.google_service.verify_id_token") as mock_verify_id:
            mock_verify_id.return_value = {"sub": "test", "email": "test@example.com"}

            result = await verify_google_token("mock.jwt.token.here")

            assert result is not None
            mock_verify_id.assert_called_once_with("mock.jwt.token.here")