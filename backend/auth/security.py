"""
Security Utilities for Authentication
Password hashing and JWT token management
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password from user
        hashed_password: Bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    """
    Create a JWT access or refresh token

    Args:
        subject: Subject (usually user_id as string)
        expires_delta: Token expiration time (default: 1 hour for access, 7 days for refresh)
        token_type: "access" or "refresh"

    Returns:
        Encoded JWT token
    """
    settings = get_settings()

    if expires_delta is None:
        # Default expiration times
        if token_type == "access":
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        else:  # refresh
            expires_delta = timedelta(days=settings.refresh_token_expire_days)

    expire = datetime.utcnow() + expires_delta

    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token

    Args:
        token: Encoded JWT token

    Returns:
        Decoded token payload or None if invalid

    Raises:
        JWTError: If token is invalid or expired
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise
