"""
Unit tests for Scheduler Service
Tests the scheduler logic without full integration
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch
import pytz

from backend.core.scheduler import CommandSchedulerService
from backend.models.scheduled_command_models import (
    ScheduledCommand,
    ScheduleType,
    IntervalUnit,
)


@pytest.mark.asyncio
async def test_scheduler_initialization():
    """Test that scheduler initializes correctly"""
    scheduler = CommandSchedulerService()

    assert scheduler.scheduler is None
    assert not scheduler._initialized

    await scheduler.initialize()

    assert scheduler.scheduler is not None
    assert scheduler._initialized


@pytest.mark.asyncio
async def test_calculate_next_run_cron_schedule():
    """Test calculating next run time for cron schedules"""
    scheduler = CommandSchedulerService()

    # Create a mock schedule - daily at 9am UTC
    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * *",
        timezone="UTC",
        enabled=True,
        interval_value=None,
        interval_unit=None,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    next_run = scheduler._calculate_next_run(schedule)

    assert next_run is not None
    assert isinstance(next_run, datetime)
    # Should be in the future
    assert next_run > datetime.now(pytz.UTC)
    # Should be at 9:00 UTC
    assert next_run.hour == 9
    assert next_run.minute == 0


@pytest.mark.asyncio
async def test_calculate_next_run_interval_schedule():
    """Test calculating next run time for interval schedules"""
    scheduler = CommandSchedulerService()

    # Create a mock schedule - every 30 minutes
    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.INTERVAL,
        cron_expression=None,
        interval_value=30,
        interval_unit=IntervalUnit.MINUTES,
        timezone="UTC",
        enabled=True,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    next_run = scheduler._calculate_next_run(schedule)

    assert next_run is not None
    assert isinstance(next_run, datetime)

    # Should be approximately 30 minutes from now
    now_utc = datetime.now(pytz.UTC)
    time_diff = next_run - now_utc

    # Allow 1 minute tolerance
    assert timedelta(minutes=29) <= time_diff <= timedelta(minutes=31)


@pytest.mark.asyncio
async def test_calculate_next_run_different_timezone():
    """Test calculating next run time with different timezone"""
    scheduler = CommandSchedulerService()

    # Create a mock schedule - daily at 9am New York time
    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * *",
        timezone="America/New_York",
        enabled=True,
        interval_value=None,
        interval_unit=None,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    next_run = scheduler._calculate_next_run(schedule)

    assert next_run is not None
    # Result should be in UTC
    assert next_run.tzinfo == pytz.UTC
    # Should be in the future
    assert next_run > datetime.now(pytz.UTC)


@pytest.mark.asyncio
async def test_create_cron_trigger():
    """Test creating a cron trigger from schedule"""
    scheduler = CommandSchedulerService()

    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * 1-5",  # Weekdays at 9am
        timezone="UTC",
        enabled=True,
        interval_value=None,
        interval_unit=None,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    trigger = scheduler._create_trigger(schedule)

    assert trigger is not None
    assert trigger.__class__.__name__ == "CronTrigger"


@pytest.mark.asyncio
async def test_create_interval_trigger():
    """Test creating an interval trigger from schedule"""
    scheduler = CommandSchedulerService()

    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.INTERVAL,
        cron_expression=None,
        interval_value=60,
        interval_unit=IntervalUnit.MINUTES,
        timezone="UTC",
        enabled=True,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    trigger = scheduler._create_trigger(schedule)

    assert trigger is not None
    assert trigger.__class__.__name__ == "IntervalTrigger"


@pytest.mark.asyncio
async def test_invalid_cron_expression():
    """Test handling of invalid cron expression"""
    scheduler = CommandSchedulerService()

    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.CRON,
        cron_expression="invalid cron",
        timezone="UTC",
        enabled=True,
        interval_value=None,
        interval_unit=None,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    trigger = scheduler._create_trigger(schedule)

    # Should return None for invalid cron expression
    assert trigger is None


@pytest.mark.asyncio
async def test_scheduler_status_not_initialized():
    """Test scheduler status when not initialized"""
    scheduler = CommandSchedulerService()

    status = scheduler.get_scheduler_status()

    assert status['running'] is False
    assert status['initialized'] is False
    assert status['jobs_count'] == 0
    assert status['jobs'] == []


@pytest.mark.asyncio
async def test_scheduler_status_initialized():
    """Test scheduler status after initialization"""
    scheduler = CommandSchedulerService()
    await scheduler.initialize()

    status = scheduler.get_scheduler_status()

    assert status['initialized'] is True
    assert 'running' in status
    assert 'jobs_count' in status
    assert 'jobs' in status


@pytest.mark.asyncio
async def test_calculate_next_run_hourly_interval():
    """Test calculating next run for hourly interval"""
    scheduler = CommandSchedulerService()

    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.INTERVAL,
        cron_expression=None,
        interval_value=2,
        interval_unit=IntervalUnit.HOURS,
        timezone="UTC",
        enabled=True,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    next_run = scheduler._calculate_next_run(schedule)

    assert next_run is not None

    # Should be approximately 2 hours from now
    now_utc = datetime.now(pytz.UTC)
    time_diff = next_run - now_utc

    # Allow 1 minute tolerance
    assert timedelta(hours=1, minutes=59) <= time_diff <= timedelta(hours=2, minutes=1)


@pytest.mark.asyncio
async def test_calculate_next_run_daily_interval():
    """Test calculating next run for daily interval"""
    scheduler = CommandSchedulerService()

    schedule = ScheduledCommand(
        id=uuid4(),
        user_id=uuid4(),
        command_text="@test task",
        agent_id="agent_test",
        agent_nickname="test",
        schedule_type=ScheduleType.INTERVAL,
        cron_expression=None,
        interval_value=1,
        interval_unit=IntervalUnit.DAYS,
        timezone="UTC",
        enabled=True,
        max_retries=3,
        retry_delay_minutes=5,
        timeout_seconds=300,
        description=None,
        tags=[],
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    next_run = scheduler._calculate_next_run(schedule)

    assert next_run is not None

    # Should be approximately 1 day from now
    now_utc = datetime.now(pytz.UTC)
    time_diff = next_run - now_utc

    # Allow 1 minute tolerance
    assert timedelta(days=1, minutes=-1) <= time_diff <= timedelta(days=1, minutes=1)
