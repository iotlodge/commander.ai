"""
Tests for security utilities (password hashing, JWT tokens)
"""
import pytest
from datetime import timedelta
from jose import jwt, JWTError

from backend.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)
from backend.core.config import get_settings


def test_password_hashing():
    """Test password hashing and verification"""
    password = "mysecretpassword123"
    hashed = get_password_hash(password)

    # Hash should be different from password
    assert hashed != password

    # Hash should be long (bcrypt hashes are 60 chars)
    assert len(hashed) > 50

    # Should verify correctly
    assert verify_password(password, hashed) is True

    # Should fail with wrong password
    assert verify_password("wrongpassword", hashed) is False


def test_password_hash_unique():
    """Test that same password produces different hashes (salt)"""
    password = "samepassword"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Hashes should be different due to different salts
    assert hash1 != hash2

    # Both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_create_access_token():
    """Test JWT access token creation"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(subject=user_id, token_type="access")

    assert isinstance(token, str)
    assert len(token) > 20

    # Decode and verify payload
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token():
    """Test JWT refresh token creation"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(subject=user_id, token_type="refresh")

    # Decode and verify payload
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_token_custom_expiration():
    """Test token with custom expiration"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    expires_delta = timedelta(minutes=30)

    token = create_access_token(
        subject=user_id,
        expires_delta=expires_delta,
        token_type="access",
    )

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id


def test_decode_invalid_token():
    """Test decoding invalid token raises error"""
    with pytest.raises(JWTError):
        decode_token("invalid-token-string")


def test_decode_token_wrong_algorithm():
    """Test decoding token with wrong algorithm fails"""
    settings = get_settings()

    # Create token with different algorithm
    payload = {"sub": "test", "type": "access"}
    wrong_token = jwt.encode(payload, settings.secret_key, algorithm="HS512")

    with pytest.raises(JWTError):
        decode_token(wrong_token)


def test_decode_token_wrong_secret():
    """Test decoding token with wrong secret fails"""
    # Create token with different secret
    payload = {"sub": "test", "type": "access"}
    wrong_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

    with pytest.raises(JWTError):
        decode_token(wrong_token)


def test_token_expiration_claim():
    """Test that tokens include expiration timestamp"""
    import time

    user_id = "123e4567-e89b-12d3-a456-426614174000"
    before_creation = int(time.time())

    token = create_access_token(subject=user_id, token_type="access")
    payload = decode_token(token)

    after_creation = int(time.time())

    # Expiration should be in the future
    assert payload["exp"] > after_creation

    # Should be roughly 1 hour from now (default access token expiry)
    expected_exp = before_creation + (60 * 60)  # 1 hour
    assert abs(payload["exp"] - expected_exp) < 60  # Within 1 minute tolerance
