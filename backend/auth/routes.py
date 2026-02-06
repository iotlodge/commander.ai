"""
Authentication API Routes
Endpoints for user registration, login, and token management
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_active_user
from backend.auth.models import User
from backend.auth.schemas import (
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from backend.auth.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.core.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Register a new user account

    Args:
        user_data: User registration data (email, password)
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException: 400 if email already registered
    """
    # Check if user already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"New user registered: {new_user.email} (ID: {new_user.id})")
        return new_user

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Token:
    """
    Authenticate user and return JWT tokens

    Args:
        login_data: User login credentials (email, password)
        db: Database session

    Returns:
        JWT access and refresh tokens

    Raises:
        HTTPException: 401 if credentials invalid
    """
    # Fetch user by email
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive account",
        )

    # Create access and refresh tokens
    access_token = create_access_token(subject=str(user.id), token_type="access")
    refresh_token = create_access_token(subject=str(user.id), token_type="refresh")

    logger.info(f"User logged in: {user.email} (ID: {user.id})")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Token:
    """
    Refresh access token using refresh token

    Args:
        refresh_data: Refresh token
        db: Database session

    Returns:
        New JWT access and refresh tokens

    Raises:
        HTTPException: 401 if refresh token invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode refresh token
        payload = decode_token(refresh_data.refresh_token)
        if payload is None:
            raise credentials_exception

        # Verify token type is "refresh"
        token_type: str | None = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract user_id
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Verify user exists and is active
        stmt = select(User).where(User.id == user_id_str)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise credentials_exception

        # Create new tokens
        access_token = create_access_token(subject=str(user.id), token_type="access")
        new_refresh_token = create_access_token(subject=str(user.id), token_type="refresh")

        logger.info(f"Tokens refreshed for user: {user.email} (ID: {user.id})")

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    except JWTError as e:
        logger.warning(f"Refresh token validation failed: {e}")
        raise credentials_exception


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        User information
    """
    return current_user
