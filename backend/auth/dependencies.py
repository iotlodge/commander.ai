"""
FastAPI Dependencies for Authentication
Dependency injection for protected routes
"""

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import User
from backend.auth.security import decode_token
from backend.core.database import get_db_session
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme (auto_error=False for optional auth)
security = HTTPBearer(auto_error=False)

# MVP User ID for development bypass
MVP_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: Optional[str] = Query(None, description="User ID for development bypass"),
) -> User:
    """
    Get current authenticated user from JWT token or development bypass

    In development, allows MVP_USER_ID via query parameter for frontend compatibility.
    In production, requires valid JWT token.

    Args:
        credentials: HTTP Bearer credentials from Authorization header (optional)
        db: Database session
        user_id: Optional user_id query param for MVP user bypass

    Returns:
        User object if authentication successful

    Raises:
        HTTPException: 401/403 if authentication fails
    """
    settings = get_settings()

    # Development bypass: Allow MVP_USER_ID via query parameter
    if user_id and user_id == str(MVP_USER_ID):
        logger.info("Development bypass: Using MVP_USER_ID from query parameter")
        stmt = select(User).where(User.id == MVP_USER_ID)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            # Create MVP user if it doesn't exist (development only)
            from backend.auth.security import get_password_hash
            user = User(
                id=MVP_USER_ID,
                email="mvp@commander.ai",
                hashed_password=get_password_hash("mvp_password"),
                is_active=True,
                is_superuser=False,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("Created MVP user for development")

        return user

    # Production: Require JWT token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated. Please provide Bearer token.",
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token from credentials
        token = credentials.credentials

        # Decode JWT token
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception

        # Extract user_id from token subject
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Verify token type is "access"
        token_type: str | None = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_user_id = UUID(user_id_str)

    except (JWTError, ValueError) as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception

    # Fetch user from database
    stmt = select(User).where(User.id == token_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User not found for user_id: {token_user_id}")
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current authenticated user and verify account is active

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User object if account is active

    Raises:
        HTTPException: 400 if account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive account",
        )
    return current_user
