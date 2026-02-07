"""
Unit tests for Scheduled Command Repository
Tests CRUD operations for scheduled commands and executions
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy import JSON, String

from backend.models.base import Base
from backend.repositories.scheduled_command_repository import (
    ScheduledCommandRepository,
    ScheduledCommandModel,
    ScheduledCommandExecutionModel,
)
from backend.models.scheduled_command_models import (
    ScheduledCommandCreate,
    ScheduledCommandUpdate,
    ScheduledCommandExecutionCreate,
    ScheduledCommandExecutionUpdate,
    ScheduleType,
    IntervalUnit,
    ExecutionStatus,
)


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
        for table in Base.metadata.tables.values():
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
                    # Remove NOW(), gen_random_uuid(), and ::jsonb casts
                    if ('NOW()' in server_default_text or
                        'gen_random_uuid()' in server_default_text or
                        '::jsonb' in server_default_text):
                        column.server_default = None

        await conn.run_sync(Base.metadata.create_all)

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
def sample_user_id():
    """Sample user ID for testing"""
    return uuid4()


@pytest.fixture
def sample_cron_command(sample_user_id):
    """Sample cron-based scheduled command"""
    return ScheduledCommandCreate(
        user_id=sample_user_id,
        command_text="@alice check deprecated models",
        agent_id="agent_alice",
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * 1-5",  # Weekdays at 9am
        timezone="America/New_York",
        description="Daily model deprecation check",
        tags=["maintenance", "models"],
    )


@pytest.fixture
def sample_interval_command(sample_user_id):
    """Sample interval-based scheduled command"""
    return ScheduledCommandCreate(
        user_id=sample_user_id,
        command_text="@bob search latest AI news",
        agent_id="agent_bob",
        schedule_type=ScheduleType.INTERVAL,
        interval_value=30,
        interval_unit=IntervalUnit.MINUTES,
        description="Regular news check",
        tags=["research"],
    )


# === Scheduled Command Tests ===


@pytest.mark.asyncio
async def test_create_cron_scheduled_command(test_session, sample_cron_command):
    """Test creating a cron-based scheduled command"""
    repo = ScheduledCommandRepository(test_session)

    # Mock AgentRegistry to avoid dependency issues in tests
    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_cron_command)

    assert command.id is not None
    assert command.user_id == sample_cron_command.user_id
    assert command.command_text == sample_cron_command.command_text
    assert command.agent_id == sample_cron_command.agent_id
    assert command.agent_nickname == "alice"
    assert command.schedule_type == ScheduleType.CRON
    assert command.cron_expression == "0 9 * * 1-5"
    assert command.timezone == "America/New_York"
    assert command.enabled is True
    assert command.description == "Daily model deprecation check"
    assert "maintenance" in command.tags


@pytest.mark.asyncio
async def test_create_interval_scheduled_command(test_session, sample_interval_command):
    """Test creating an interval-based scheduled command"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "bob"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_interval_command)

    assert command.id is not None
    assert command.schedule_type == ScheduleType.INTERVAL
    assert command.interval_value == 30
    assert command.interval_unit == IntervalUnit.MINUTES
    assert command.agent_nickname == "bob"


@pytest.mark.asyncio
async def test_get_scheduled_command(test_session, sample_cron_command):
    """Test retrieving a scheduled command by ID"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        created = await repo.create_scheduled_command(sample_cron_command)

    # Retrieve by ID
    retrieved = await repo.get_scheduled_command(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.command_text == created.command_text
    assert retrieved.cron_expression == created.cron_expression


@pytest.mark.asyncio
async def test_get_nonexistent_command(test_session):
    """Test retrieving a non-existent command returns None"""
    repo = ScheduledCommandRepository(test_session)

    result = await repo.get_scheduled_command(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_user_scheduled_commands(test_session, sample_user_id):
    """Test retrieving all commands for a user"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        # Create multiple commands
        command1 = ScheduledCommandCreate(
            user_id=sample_user_id,
            command_text="@alice task 1",
            agent_id="agent_alice",
            schedule_type=ScheduleType.CRON,
            cron_expression="0 9 * * *",
        )
        command2 = ScheduledCommandCreate(
            user_id=sample_user_id,
            command_text="@alice task 2",
            agent_id="agent_alice",
            schedule_type=ScheduleType.INTERVAL,
            interval_value=60,
            interval_unit=IntervalUnit.MINUTES,
            enabled=False,  # Disabled
        )

        await repo.create_scheduled_command(command1)
        await repo.create_scheduled_command(command2)

    # Get all commands
    all_commands = await repo.get_user_scheduled_commands(sample_user_id)
    assert len(all_commands) == 2

    # Get only enabled commands
    enabled_commands = await repo.get_user_scheduled_commands(sample_user_id, enabled_only=True)
    assert len(enabled_commands) == 1
    assert enabled_commands[0].enabled is True


@pytest.mark.asyncio
async def test_get_user_commands_filtered_by_agent(test_session, sample_user_id):
    """Test retrieving commands filtered by agent_id"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "test"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        # Create commands for different agents
        await repo.create_scheduled_command(
            ScheduledCommandCreate(
                user_id=sample_user_id,
                command_text="@alice task",
                agent_id="agent_alice",
                schedule_type=ScheduleType.CRON,
                cron_expression="0 9 * * *",
            )
        )
        await repo.create_scheduled_command(
            ScheduledCommandCreate(
                user_id=sample_user_id,
                command_text="@bob task",
                agent_id="agent_bob",
                schedule_type=ScheduleType.CRON,
                cron_expression="0 10 * * *",
            )
        )

    # Get commands for specific agent
    alice_commands = await repo.get_user_scheduled_commands(sample_user_id, agent_id="agent_alice")
    assert len(alice_commands) == 1
    assert alice_commands[0].agent_id == "agent_alice"


@pytest.mark.asyncio
async def test_update_scheduled_command(test_session, sample_cron_command):
    """Test updating a scheduled command"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        created = await repo.create_scheduled_command(sample_cron_command)

    # Update command
    update = ScheduledCommandUpdate(
        command_text="@alice updated task",
        cron_expression="0 10 * * *",  # Changed time
        description="Updated description",
        enabled=False,
    )

    updated = await repo.update_scheduled_command(created.id, update)

    assert updated is not None
    assert updated.command_text == "@alice updated task"
    assert updated.cron_expression == "0 10 * * *"
    assert updated.description == "Updated description"
    assert updated.enabled is False


@pytest.mark.asyncio
async def test_update_next_run(test_session, sample_cron_command):
    """Test updating next_run_at and last_run_at"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        created = await repo.create_scheduled_command(sample_cron_command)

    # Update run times
    next_run = datetime.utcnow() + timedelta(hours=1)
    last_run = datetime.utcnow()

    await repo.update_next_run(
        created.id,
        next_run_at=next_run,
        last_run_at=last_run,
        last_run_status=ExecutionStatus.SUCCESS,
    )

    # Verify update
    updated = await repo.get_scheduled_command(created.id)
    assert updated.next_run_at is not None
    assert updated.last_run_at is not None
    assert updated.last_run_status == ExecutionStatus.SUCCESS


@pytest.mark.asyncio
async def test_delete_scheduled_command(test_session, sample_cron_command):
    """Test deleting a scheduled command"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        created = await repo.create_scheduled_command(sample_cron_command)

    # Delete command
    deleted = await repo.delete_scheduled_command(created.id)
    assert deleted is True

    # Verify deletion
    retrieved = await repo.get_scheduled_command(created.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_count_user_schedules(test_session, sample_user_id):
    """Test counting schedules for a user"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        # Create 3 commands
        for i in range(3):
            await repo.create_scheduled_command(
                ScheduledCommandCreate(
                    user_id=sample_user_id,
                    command_text=f"@alice task {i}",
                    agent_id="agent_alice",
                    schedule_type=ScheduleType.CRON,
                    cron_expression="0 9 * * *",
                )
            )

    count = await repo.count_user_schedules(sample_user_id)
    assert count == 3


# === Execution Tests ===


@pytest.mark.asyncio
async def test_create_execution(test_session, sample_cron_command):
    """Test creating an execution record"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_cron_command)

    # Create execution
    execution_create = ScheduledCommandExecutionCreate(
        scheduled_command_id=command.id,
        task_id=uuid4(),
    )

    execution = await repo.create_execution(execution_create)

    assert execution.id is not None
    assert execution.scheduled_command_id == command.id
    assert execution.task_id == execution_create.task_id
    assert execution.status == ExecutionStatus.PENDING
    assert execution.triggered_at is not None


@pytest.mark.asyncio
async def test_get_execution(test_session, sample_cron_command):
    """Test retrieving an execution by ID"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_cron_command)

    execution_create = ScheduledCommandExecutionCreate(
        scheduled_command_id=command.id
    )
    created = await repo.create_execution(execution_create)

    # Retrieve by ID
    retrieved = await repo.get_execution(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.scheduled_command_id == command.id


@pytest.mark.asyncio
async def test_get_command_executions(test_session, sample_cron_command):
    """Test retrieving execution history for a command"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_cron_command)

    # Create multiple executions
    for i in range(5):
        await repo.create_execution(
            ScheduledCommandExecutionCreate(
                scheduled_command_id=command.id
            )
        )

    executions = await repo.get_command_executions(command.id, limit=10)

    assert len(executions) == 5
    # Should be ordered by triggered_at DESC (most recent first)
    assert executions[0].triggered_at >= executions[-1].triggered_at


@pytest.mark.asyncio
async def test_update_execution(test_session, sample_cron_command):
    """Test updating an execution record"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_cron_command)

    execution = await repo.create_execution(
        ScheduledCommandExecutionCreate(
            scheduled_command_id=command.id
        )
    )

    # Update execution
    now = datetime.utcnow()
    update = ScheduledCommandExecutionUpdate(
        started_at=now,
        completed_at=now + timedelta(seconds=5),
        status=ExecutionStatus.SUCCESS,
        result_summary="Task completed successfully",
        execution_duration_ms=5000,
        tokens_used=1500,
        llm_calls=3,
    )

    updated = await repo.update_execution(execution.id, update)

    assert updated is not None
    assert updated.status == ExecutionStatus.SUCCESS
    assert updated.result_summary == "Task completed successfully"
    assert updated.execution_duration_ms == 5000
    assert updated.tokens_used == 1500
    assert updated.llm_calls == 3


@pytest.mark.asyncio
async def test_execution_error_tracking(test_session, sample_cron_command):
    """Test tracking execution errors and retries"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        command = await repo.create_scheduled_command(sample_cron_command)

    execution = await repo.create_execution(
        ScheduledCommandExecutionCreate(
            scheduled_command_id=command.id
        )
    )

    # Update with error
    update = ScheduledCommandExecutionUpdate(
        status=ExecutionStatus.FAILED,
        error_message="Agent timeout",
        retry_count=2,
    )

    updated = await repo.update_execution(execution.id, update)

    assert updated.status == ExecutionStatus.FAILED
    assert updated.error_message == "Agent timeout"
    assert updated.retry_count == 2


@pytest.mark.asyncio
async def test_get_enabled_scheduled_commands(test_session, sample_user_id):
    """Test retrieving all enabled commands for scheduler initialization"""
    repo = ScheduledCommandRepository(test_session)

    from unittest.mock import patch, MagicMock
    mock_agent = MagicMock()
    mock_agent.nickname = "alice"

    with patch('backend.agents.base.agent_registry.AgentRegistry.get_specialist', return_value=mock_agent):
        # Create enabled and disabled commands
        await repo.create_scheduled_command(
            ScheduledCommandCreate(
                user_id=sample_user_id,
                command_text="@alice enabled task",
                agent_id="agent_alice",
                schedule_type=ScheduleType.CRON,
                cron_expression="0 9 * * *",
                enabled=True,
            )
        )
        await repo.create_scheduled_command(
            ScheduledCommandCreate(
                user_id=sample_user_id,
                command_text="@alice disabled task",
                agent_id="agent_alice",
                schedule_type=ScheduleType.CRON,
                cron_expression="0 10 * * *",
                enabled=False,
            )
        )

    enabled = await repo.get_enabled_scheduled_commands()

    assert len(enabled) == 1
    assert enabled[0].enabled is True
