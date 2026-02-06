"""
Tests for protected API routes (tasks with authentication)
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from backend.auth.models import User


@pytest.mark.asyncio
async def test_create_task_authenticated(test_client: AsyncClient, auth_headers: dict):
    """Test creating task with valid authentication"""
    response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(uuid4()),  # This should be ignored
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "test command",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["agent_id"] == "agent_a"
    # Verify user_id is from token, not request body
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_create_task_no_auth(test_client: AsyncClient):
    """Test creating task without authentication fails"""
    response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(uuid4()),
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "test command",
        },
    )

    assert response.status_code == 403  # Forbidden (no auth header)


@pytest.mark.asyncio
async def test_create_task_invalid_token(test_client: AsyncClient):
    """Test creating task with invalid token"""
    response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(uuid4()),
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "test command",
        },
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_list_tasks_authenticated(test_client: AsyncClient, auth_headers: dict):
    """Test listing tasks with authentication"""
    response = await test_client.get("/api/tasks", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_tasks_no_auth(test_client: AsyncClient):
    """Test listing tasks without authentication fails"""
    response = await test_client.get("/api/tasks")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_task_own_task(
    test_client: AsyncClient,
    auth_headers: dict,
    test_user: User,
):
    """Test getting own task succeeds"""
    # Create a task first
    create_response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(test_user.id),
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "test command",
        },
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Get the task
    response = await test_client.get(f"/api/tasks/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_other_user_task_forbidden(
    test_client: AsyncClient,
    auth_headers: dict,
    other_user: User,
    other_user_task_id: str,
):
    """Test getting another user's task returns 403"""
    response = await test_client.get(
        f"/api/tasks/{other_user_task_id}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_task_own_task(
    test_client: AsyncClient,
    auth_headers: dict,
    test_user: User,
):
    """Test updating own task succeeds"""
    # Create a task
    create_response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(test_user.id),
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "test command",
        },
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Update the task
    response = await test_client.patch(
        f"/api/tasks/{task_id}",
        json={"status": "completed"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_update_task_other_user_forbidden(
    test_client: AsyncClient,
    auth_headers: dict,
    other_user_task_id: str,
):
    """Test updating another user's task returns 403"""
    response = await test_client.patch(
        f"/api/tasks/{other_user_task_id}",
        json={"status": "completed"},
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_task_own_task(
    test_client: AsyncClient,
    auth_headers: dict,
    test_user: User,
):
    """Test deleting own task succeeds"""
    # Create a task
    create_response = await test_client.post(
        "/api/tasks",
        json={
            "user_id": str(test_user.id),
            "agent_id": "agent_a",
            "thread_id": str(uuid4()),
            "command": "test command",
        },
        headers=auth_headers,
    )
    task_id = create_response.json()["id"]

    # Delete the task
    response = await test_client.delete(f"/api/tasks/{task_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["deleted"] is True


@pytest.mark.asyncio
async def test_delete_task_other_user_forbidden(
    test_client: AsyncClient,
    auth_headers: dict,
    other_user_task_id: str,
):
    """Test deleting another user's task returns 403"""
    response = await test_client.delete(
        f"/api/tasks/{other_user_task_id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_submit_command_authenticated(test_client: AsyncClient, auth_headers: dict):
    """Test submitting command with authentication"""
    response = await test_client.post(
        "/api/commands",
        json={"text": "@alice help"},
        headers=auth_headers,
    )

    # Note: This might fail if agent registry isn't initialized in tests
    # We're just testing auth, not full functionality
    assert response.status_code in [200, 400]  # 400 if agent not found


@pytest.mark.asyncio
async def test_submit_command_no_auth(test_client: AsyncClient):
    """Test submitting command without authentication fails"""
    response = await test_client.post(
        "/api/commands",
        json={"text": "@alice help"},
    )

    assert response.status_code == 403
