"""
Integration tests for Task API endpoints
Tests UI<->Backend communication for task management
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# These tests require the FastAPI app
# Uncomment when ready to test:
# from backend.api.main import app


@pytest.mark.api
class TestTaskAPI:
    """Test Task API endpoints used by frontend"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        # Uncomment when ready:
        # return TestClient(app)
        pytest.skip("FastAPI app integration pending")

    def test_create_task_endpoint(self, client, test_user_id):
        """Test POST /api/v1/tasks - Create new task"""
        response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "@bob research quantum computing",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert data["agent_id"] == "agent_a"
        assert data["agent_nickname"] == "bob"

    def test_get_task_status(self, client, test_user_id):
        """Test GET /api/v1/tasks/{task_id} - Get task status"""
        # Create task first
        create_response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "@sue review compliance",
            },
        )
        task_id = create_response.json()["task_id"]

        # Get status
        response = client.get(f"/api/v1/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == task_id
        assert "status" in data
        assert "progress_percentage" in data
        assert "current_node" in data

    def test_list_user_tasks(self, client, test_user_id):
        """Test GET /api/v1/tasks?user_id={user_id} - List user tasks"""
        # Create multiple tasks
        for agent in ["@bob", "@sue", "@rex"]:
            client.post(
                "/api/v1/tasks",
                json={
                    "user_id": str(test_user_id),
                    "command": f"{agent} test command",
                },
            )

        # List tasks
        response = client.get(f"/api/v1/tasks?user_id={test_user_id}")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3
        assert all("task_id" in task for task in data)

    def test_cancel_task(self, client, test_user_id):
        """Test DELETE /api/v1/tasks/{task_id} - Cancel task"""
        # Create task
        create_response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "@kai solve complex problem",
            },
        )
        task_id = create_response.json()["task_id"]

        # Cancel task
        response = client.delete(f"/api/v1/tasks/{task_id}")

        assert response.status_code == 200

        # Verify cancellation
        status_response = client.get(f"/api/v1/tasks/{task_id}")
        assert status_response.json()["status"] == "cancelled"

    def test_invalid_command_format(self, client, test_user_id):
        """Test that invalid command format returns 400"""
        response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "no agent specified",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_unknown_agent(self, client, test_user_id):
        """Test that unknown agent returns 400"""
        response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "@unknown do something",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "unknown agent" in data["error"].lower()


@pytest.mark.api
class TestTaskMetrics:
    """Test task metrics and execution tracking"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        pytest.skip("FastAPI app integration pending")

    def test_task_metrics_structure(self, client, test_user_id):
        """Test that task includes proper metrics structure"""
        response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "@bob research test",
            },
        )

        task_id = response.json()["task_id"]

        # Wait for task completion
        import time
        time.sleep(5)

        # Get completed task
        status_response = client.get(f"/api/v1/tasks/{task_id}")
        task = status_response.json()

        # Verify metrics structure
        assert "metadata" in task
        metadata = task["metadata"]

        assert "execution_metrics" in metadata
        metrics = metadata["execution_metrics"]

        assert "llm_calls" in metrics
        assert "tool_calls" in metrics
        assert "agent_calls" in metrics
        assert "tokens" in metrics
        assert "prompt" in metrics["tokens"]
        assert "completion" in metrics["tokens"]
        assert "total" in metrics["tokens"]

    def test_llm_call_tracking(self, client, test_user_id):
        """Test that LLM calls are tracked with details"""
        response = client.post(
            "/api/v1/tasks",
            json={
                "user_id": str(test_user_id),
                "command": "@maya review this is a test",
            },
        )

        task_id = response.json()["task_id"]

        # Wait for completion
        import time
        time.sleep(5)

        # Get task metrics
        status_response = client.get(f"/api/v1/tasks/{task_id}")
        metrics = status_response.json()["metadata"]["execution_metrics"]

        # Verify LLM call details
        assert metrics["llm_calls"] > 0
        assert "details" in metrics
        assert "llm_calls" in metrics["details"]

        # Check individual LLM call tracking
        llm_calls = metrics["details"]["llm_calls"]
        assert isinstance(llm_calls, list)
        assert len(llm_calls) > 0

        # Verify structure of individual call
        call = llm_calls[0]
        assert "model" in call
        assert "prompt_tokens" in call
        assert "completion_tokens" in call
        assert "purpose" in call
