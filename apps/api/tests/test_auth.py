"""Auth tests with mocked JWKS — no network."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.auth import _frontend_api, _jwks_url, verify_clerk_token


def test_frontend_api_from_key():
    assert _frontend_api().startswith("https://")
    assert _jwks_url().endswith("/.well-known/jwks.json")


@patch("app.auth._jwks_client")
def test_verify_valid_token(mock_jwks):
    mock_jwks.return_value.get_signing_key_from_jwt.return_value.key = "fake-key"
    with patch("app.auth.jwt.decode", return_value={"sub": "user_123"}):
        claims = verify_clerk_token("valid-token")
    assert claims["sub"] == "user_123"


@patch("app.auth._jwks_client")
def test_verify_invalid_token_raises(mock_jwks):
    import jwt as jwt_lib

    mock_jwks.return_value.get_signing_key_from_jwt.side_effect = jwt_lib.PyJWTError("bad token")
    with pytest.raises(HTTPException) as exc:
        verify_clerk_token("garbage")
    assert exc.value.status_code == 401
