"""
Tests for authentication routes (register, login, refresh, /me)
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import User
from backend.auth.security import get_password_hash


@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient):
    """Test successful user registration"""
    response = await test_client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data  # Should not expose password


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client: AsyncClient, test_user: User):
    """Test registration with already registered email"""
    response = await test_client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpassword123",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(test_client: AsyncClient):
    """Test registration with invalid email format"""
    response = await test_client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_weak_password(test_client: AsyncClient):
    """Test registration with password too short"""
    response = await test_client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",  # Less than 8 characters
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, test_user: User):
    """Test successful login"""
    response = await test_client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123",  # From fixture
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify tokens are not empty
    assert len(data["access_token"]) > 20
    assert len(data["refresh_token"]) > 20


@pytest.mark.asyncio
async def test_login_wrong_password(test_client: AsyncClient, test_user: User):
    """Test login with incorrect password"""
    response = await test_client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(test_client: AsyncClient):
    """Test login with non-existent email"""
    response = await test_client.post(
        "/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "anypassword",
        },
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_inactive_user(test_client: AsyncClient, db_session: AsyncSession):
    """Test login with inactive user account"""
    from backend.auth.security import get_password_hash

    # Create inactive user
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.commit()

    response = await test_client.post(
        "/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_current_user_me(test_client: AsyncClient, auth_headers: dict):
    """Test GET /auth/me endpoint"""
    response = await test_client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_current_user_me_no_token(test_client: AsyncClient):
    """Test GET /auth/me without authentication"""
    response = await test_client.get("/auth/me")

    assert response.status_code == 403  # FastAPI returns 403 for missing auth


@pytest.mark.asyncio
async def test_get_current_user_me_invalid_token(test_client: AsyncClient):
    """Test GET /auth/me with invalid token"""
    response = await test_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token-here"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(test_client: AsyncClient, test_user: User):
    """Test successful token refresh"""
    import asyncio

    # Login to get tokens
    login_response = await test_client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    # Wait 1 second to ensure different expiration timestamp
    await asyncio.sleep(1)

    # Refresh tokens
    response = await test_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # New tokens should be different from old ones (due to different exp timestamp)
    assert data["access_token"] != login_response.json()["access_token"]
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_with_access_token(test_client: AsyncClient, test_user: User):
    """Test refresh endpoint rejects access tokens"""
    # Login to get tokens
    login_response = await test_client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123",
        },
    )
    access_token = login_response.json()["access_token"]

    # Try to refresh with access token (should fail)
    response = await test_client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401
    assert "invalid token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token_invalid(test_client: AsyncClient):
    """Test refresh with invalid token"""
    response = await test_client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401
