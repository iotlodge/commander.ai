"""
API Integration tests for Scheduled Commands REST endpoints
Tests the complete HTTP API for schedule management
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy import JSON, String

from backend.models.base import Base
from backend.api.main import app
from backend.repositories.task_repository import get_db_session
from backend.models.scheduled_command_models import ScheduleType, IntervalUnit


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create test database engine with SQLite compatibility fixes"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Replace PostgreSQL-specific types with SQLite-compatible types
    async with engine.begin() as conn:
        from sqlalchemy.dialects.postgresql import ARRAY
        from backend.repositories.scheduled_command_repository import (
            ScheduledCommandModel,
            ScheduledCommandExecutionModel,
        )

        # Only fix the tables we're testing
        tables_to_create = [
            ScheduledCommandModel.__table__,
            ScheduledCommandExecutionModel.__table__,
        ]

        for table in tables_to_create:
            for column in table.columns:
                # Replace JSONB with JSON
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                # Replace PostgreSQL UUID with String
                if isinstance(column.type, PGUUID):
                    column.type = String(36)
                # Remove PostgreSQL-specific server defaults
                if column.server_default and hasattr(column.server_default, 'arg'):
                    server_default_text = str(column.server_default.arg)
                    if ('NOW()' in server_default_text or
                        'gen_random_uuid()' in server_default_text or
                        '::jsonb' in server_default_text):
                        column.server_default = None

        # Create only our tables
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=tables_to_create,
                checkfirst=True
            )
        )

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def test_client(test_session):
    """Create test HTTP client with database override"""
    async def override_get_db_session():
        yield test_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "00000000-0000-0000-0000-000000000001"  # MVP user ID


@pytest.mark.asyncio
async def test_create_cron_schedule(test_client, sample_user_id):
    """Test creating a cron-based schedule via API"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice daily check",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 9 * * *",
                "timezone": "UTC",
                "description": "Daily morning check",
            }
        )

    assert response.status_code == 200
    data = response.json()

    assert data['command_text'] == "@alice daily check"
    assert data['schedule_type'] == "cron"
    assert data['cron_expression'] == "0 9 * * *"
    assert data['enabled'] is True


@pytest.mark.asyncio
async def test_create_interval_schedule(test_client, sample_user_id):
    """Test creating an interval-based schedule via API"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "bob"
        mock_get.return_value = mock_agent

        response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@bob periodic search",
                "agent_id": "agent_bob",
                "schedule_type": "interval",
                "interval_value": 30,
                "interval_unit": "minutes",
                "description": "Regular search updates",
            }
        )

    assert response.status_code == 200
    data = response.json()

    assert data['command_text'] == "@bob periodic search"
    assert data['schedule_type'] == "interval"
    assert data['interval_value'] == 30
    assert data['interval_unit'] == "minutes"


@pytest.mark.asyncio
async def test_list_schedules(test_client, sample_user_id):
    """Test listing schedules for a user"""
    # Create two schedules first
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task 1",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 9 * * *",
            }
        )

        await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task 2",
                "agent_id": "agent_alice",
                "schedule_type": "interval",
                "interval_value": 60,
                "interval_unit": "minutes",
            }
        )

    # List schedules
    response = await test_client.get(f"/api/scheduled-commands?user_id={sample_user_id}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert all(schedule['user_id'] == sample_user_id for schedule in data)


@pytest.mark.asyncio
async def test_get_schedule_by_id(test_client, sample_user_id):
    """Test retrieving a specific schedule"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create schedule
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice test",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
            }
        )

        schedule_id = create_response.json()['id']

    # Get schedule
    response = await test_client.get(
        f"/api/scheduled-commands/{schedule_id}?user_id={sample_user_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data['id'] == schedule_id
    assert data['command_text'] == "@alice test"


@pytest.mark.asyncio
async def test_update_schedule(test_client, sample_user_id):
    """Test updating a schedule"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create schedule
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice original",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 9 * * *",
            }
        )

        schedule_id = create_response.json()['id']

    # Update schedule
    response = await test_client.put(
        f"/api/scheduled-commands/{schedule_id}?user_id={sample_user_id}",
        json={
            "command_text": "@alice updated",
            "cron_expression": "0 10 * * *",
            "description": "Updated description",
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data['command_text'] == "@alice updated"
    assert data['cron_expression'] == "0 10 * * *"
    assert data['description'] == "Updated description"


@pytest.mark.asyncio
async def test_delete_schedule(test_client, sample_user_id):
    """Test deleting a schedule"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create schedule
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice delete me",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
            }
        )

        schedule_id = create_response.json()['id']

    # Delete schedule
    response = await test_client.delete(
        f"/api/scheduled-commands/{schedule_id}?user_id={sample_user_id}"
    )

    assert response.status_code == 200

    # Verify deletion
    get_response = await test_client.get(
        f"/api/scheduled-commands/{schedule_id}?user_id={sample_user_id}"
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_enable_schedule(test_client, sample_user_id):
    """Test enabling a schedule"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create disabled schedule
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
                "enabled": False,
            }
        )

        schedule_id = create_response.json()['id']

    # Enable schedule
    response = await test_client.post(
        f"/api/scheduled-commands/{schedule_id}/enable?user_id={sample_user_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data['schedule']['enabled'] is True


@pytest.mark.asyncio
async def test_disable_schedule(test_client, sample_user_id):
    """Test disabling a schedule"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create enabled schedule
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
                "enabled": True,
            }
        )

        schedule_id = create_response.json()['id']

    # Disable schedule
    response = await test_client.post(
        f"/api/scheduled-commands/{schedule_id}/disable?user_id={sample_user_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data['schedule']['enabled'] is False


@pytest.mark.asyncio
async def test_get_scheduler_status(test_client):
    """Test getting scheduler status"""
    response = await test_client.get("/api/scheduled-commands/scheduler/status")

    assert response.status_code == 200
    data = response.json()

    assert 'running' in data
    assert 'initialized' in data
    assert 'jobs_count' in data
    assert 'jobs' in data


@pytest.mark.asyncio
async def test_filter_schedules_by_agent(test_client, sample_user_id):
    """Test filtering schedules by agent_id"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "test"
        mock_get.return_value = mock_agent

        # Create schedules for different agents
        await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
            }
        )

        await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@bob task",
                "agent_id": "agent_bob",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
            }
        )

    # Filter by agent_id
    response = await test_client.get(
        f"/api/scheduled-commands?user_id={sample_user_id}&agent_id=agent_alice"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]['agent_id'] == "agent_alice"


@pytest.mark.asyncio
async def test_filter_enabled_schedules(test_client, sample_user_id):
    """Test filtering for enabled schedules only"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create enabled and disabled schedules
        await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice enabled",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
                "enabled": True,
            }
        )

        await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice disabled",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
                "enabled": False,
            }
        )

    # Filter for enabled only
    response = await test_client.get(
        f"/api/scheduled-commands?user_id={sample_user_id}&enabled_only=true"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]['enabled'] is True


@pytest.mark.asyncio
async def test_get_execution_history(test_client, sample_user_id):
    """Test retrieving execution history"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create schedule
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
            }
        )

        schedule_id = create_response.json()['id']

    # Get execution history
    response = await test_client.get(
        f"/api/scheduled-commands/{schedule_id}/executions?user_id={sample_user_id}"
    )

    assert response.status_code == 200
    data = response.json()

    # Should be empty list initially
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_access_denied_wrong_user(test_client, sample_user_id):
    """Test that users cannot access other users' schedules"""
    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist') as mock_get:
        mock_agent = MagicMock()
        mock_agent.nickname = "alice"
        mock_get.return_value = mock_agent

        # Create schedule as user 1
        create_response = await test_client.post(
            f"/api/scheduled-commands?user_id={sample_user_id}",
            json={
                "user_id": sample_user_id,
                "command_text": "@alice task",
                "agent_id": "agent_alice",
                "schedule_type": "cron",
                "cron_expression": "0 * * * *",
            }
        )

        schedule_id = create_response.json()['id']

    # Try to access as user 2
    other_user_id = str(uuid4())
    response = await test_client.get(
        f"/api/scheduled-commands/{schedule_id}?user_id={other_user_id}"
    )

    assert response.status_code == 403
